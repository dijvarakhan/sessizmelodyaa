import asyncio
import datetime
from pyrogram import filters, types
from anony import app, db, lang, tasks


@app.on_message(filters.group & ~app.bl_users, group=1)
async def count_message(_, message: types.Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    today = datetime.date.today()
    await db.daily_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "date": str(today)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    start_of_week = today - datetime.timedelta(days=today.weekday())
    await db.weekly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "week": str(start_of_week)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    start_of_month = today.replace(day=1)
    await db.monthly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "month": str(start_of_month)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    await db.all_time_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$inc": {"count": 1}},
        upsert=True,
    )


async def get_leaderboard_text(chat_id: int, period: str, requester_id: int = None, requester_name: str = None) -> str:
    period_str = ""
    period_header = ""
    query_filter = {}
    collection = None

    today = datetime.date.today()
    if period == "daily":
        query_filter = {"chat_id": chat_id, "date": str(today)}
        collection = db.daily_messages
        period_str = "Günlük"
        period_header = "Bugün"
    elif period == "weekly":
        start_of_week = today - datetime.timedelta(days=today.weekday())
        query_filter = {"chat_id": chat_id, "week": str(start_of_week)}
        collection = db.weekly_messages
        period_str = "Haftalık"
        period_header = "bu HAFTA"
    elif period == "monthly":
        start_of_month = today.replace(day=1)
        query_filter = {"chat_id": chat_id, "month": str(start_of_month)}
        collection = db.monthly_messages
        period_str = "Aylık"
        period_header = "bu AY"
    elif period == "alltime":
        query_filter = {"chat_id": chat_id}
        collection = db.all_time_messages
        period_str = "Tüm Zamanlar"
        period_header = "TÜM ZAMANLARDA"
    else:
        return "Geçersiz süre."

    results = collection.find(query_filter).sort("count", -1).limit(20)
    
    # Cursor'ı listeye çevir
    results_list = []
    async for result in results:
        results_list.append(result)

    text = f"� Grubunuzdaki **{period_header}** en çok aktif olanlar:\n\n"
    text += "Kullanıcı → Mesaj\n"
    
    if not results_list:
        text += "😴 Henüz kimse mesaj göndermedi."
        return text

    # Kullanıcı bilgilerini toplu çek (Hata toleranslı)
    user_ids = [r.get("user_id") for r in results_list]
    users_dict = {}
    
    # Tek tek get_users çağrılarını asenkron olarak topla
    user_tasks = [app.get_users(uid) for uid in user_ids]
    user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
    
    for uid, res in zip(user_ids, user_results):
        if not isinstance(res, Exception):
            users_dict[uid] = res

    user_list = []
    requester_count = 0
    
    for i, result in enumerate(results_list):
        user_id = result.get("user_id")
        count = int(result.get("count", 0))
        
        if requester_id and user_id == requester_id:
            requester_count = count
        
        user = users_dict.get(user_id)
        if user:
            username = user.first_name
        else:
            username = "Bilinmeyen"
            
        user_list.append(f"⬜ {i + 1}. {username} : {count}")
    
    text += "\n".join(user_list)
    
    if requester_id and requester_name:
        # If requester wasn't in top 20, fetch their count separately
        if requester_count == 0:
             user_stat = await collection.find_one({"chat_id": chat_id, "user_id": requester_id})
             if user_stat:
                 requester_count = int(user_stat.get("count", 0))
        
        text += f"\n\nSenin {requester_name} : {requester_count}"
        
    return text


@app.on_message(filters.command(["top", "skor"]) & filters.group & ~app.bl_users)
@lang.language()
async def top_users(_, message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Default to Daily view
    text = await get_leaderboard_text(message.chat.id, "daily", user_id, user_name)
    
    # Daily view buttons: [Back] [Weekly]
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("🔙 Önceki menü", callback_data="top_close"),
                types.InlineKeyboardButton("📅 Haftalık", callback_data="top_weekly"),
            ]
        ]
    )
    await message.reply_text(text, reply_markup=markup)


@app.on_callback_query(filters.regex(r"^top_") & ~app.bl_users)
async def top_callback(_, query: types.CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    data = query.data
    
    if data == "top_close":
        await query.message.delete()
        return

    period = ""
    markup = None
    
    if data == "top_daily":
        period = "daily"
        markup = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("� Önceki menü", callback_data="top_close"),
                types.InlineKeyboardButton("� Haftalık", callback_data="top_weekly"),
            ]
        ])
    elif data == "top_weekly":
        period = "weekly"
        markup = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("� Önceki menü", callback_data="top_close"),
                types.InlineKeyboardButton("� Aylık", callback_data="top_monthly"),
            ]
        ])
    elif data == "top_monthly":
        period = "monthly"
        markup = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("� Önceki menü", callback_data="top_close"),
                types.InlineKeyboardButton("📊 Toplam", callback_data="top_alltime"),
            ]
        ])
    elif data == "top_alltime":
        period = "alltime"
        markup = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("🔙 Önceki menü", callback_data="top_close"),
                types.InlineKeyboardButton("📅 Günlük", callback_data="top_daily"),
            ]
        ])
        
    if period:
        text = await get_leaderboard_text(chat_id, period, user_id, user_name)
        try:
            await query.edit_message_text(text, reply_markup=markup)
        except Exception:
            pass



@app.on_message(filters.command(["mystats", "benimskor"]) & filters.group & ~app.bl_users)
@lang.language()
async def my_stats(_, message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    today = datetime.date.today()
    today_str = str(today)
    daily = await db.daily_messages.find_one(
        {"user_id": user_id, "chat_id": chat_id, "date": today_str}
    )
    daily_count = int(daily.get("count", 0)) if daily else 0
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly = await db.weekly_messages.find_one(
        {"user_id": user_id, "chat_id": chat_id, "week": str(start_of_week)}
    )
    weekly_count = int(weekly.get("count", 0)) if weekly else 0
    start_of_month = today.replace(day=1)
    monthly = await db.monthly_messages.find_one(
        {"user_id": user_id, "chat_id": chat_id, "month": str(start_of_month)}
    )
    monthly_count = int(monthly.get("count", 0)) if monthly else 0
    d_rank = await get_user_rank(chat_id, "daily", user_id, today_str)
    w_rank = await get_user_rank(chat_id, "weekly", user_id, str(start_of_week))
    m_rank = await get_user_rank(chat_id, "monthly", user_id, str(start_of_month))
    user = message.from_user
    text = f"**{user.mention} - Mesaj İstatistikleri**\n\n"
    text += f"📅 **Günlük:** {daily_count} mesaj"
    if d_rank > 0:
        text += f" (Sıralama: #{d_rank})"
    text += f"\n📆 **Haftalık:** {weekly_count} mesaj"
    if w_rank > 0:
        text += f" (Sıralama: #{w_rank})"
    text += f"\n🗓️ **Aylık:** {monthly_count} mesaj"
    if m_rank > 0:
        text += f" (Sıralama: #{m_rank})"
    total = daily_count + weekly_count + monthly_count
    if total > 1000:
        level = "🔥 Çok Aktif"
    elif total > 500:
        level = "⚡ Aktif"
    elif total > 100:
        level = "✨ Orta"
    else:
        level = "💤 Az Aktif"
    text += f"\n\n🏆 **Aktivite Seviyesi:** {level}"
    await message.reply_text(text)


@app.on_message(filters.command(["grupistatistik", "groupstats"]) & filters.group & ~app.bl_users)
@lang.language()
async def group_stats(_, message: types.Message):
    chat_id = message.chat.id
    today = datetime.date.today()
    today_str = str(today)
    daily_users = await db.daily_messages.count_documents(
        {"chat_id": chat_id, "date": today_str}
    )
    daily_total_list = await db.daily_messages.aggregate(
        [{"$match": {"chat_id": chat_id, "date": today_str}}, {"$group": {"_id": None, "total": {"$sum": "$count"}}}]
    ).to_list(1)
    daily_total = int(daily_total_list[0]["total"]) if daily_total_list else 0
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly_users = await db.weekly_messages.count_documents(
        {"chat_id": chat_id, "week": str(start_of_week)}
    )
    weekly_total_list = await db.weekly_messages.aggregate(
        [{"$match": {"chat_id": chat_id, "week": str(start_of_week)}}, {"$group": {"_id": None, "total": {"$sum": "$count"}}}]
    ).to_list(1)
    weekly_total = int(weekly_total_list[0]["total"]) if weekly_total_list else 0
    start_of_month = today.replace(day=1)
    monthly_users = await db.monthly_messages.count_documents(
        {"chat_id": chat_id, "month": str(start_of_month)}
    )
    monthly_total_list = await db.monthly_messages.aggregate(
        [{"$match": {"chat_id": chat_id, "month": str(start_of_month)}}, {"$group": {"_id": None, "total": {"$sum": "$count"}}}]
    ).to_list(1)
    monthly_total = int(monthly_total_list[0]["total"]) if monthly_total_list else 0
    daily_top = await db.daily_messages.find(
        {"chat_id": chat_id, "date": today_str}
    ).sort("count", -1).limit(3).to_list(3)
    weekly_top = await db.weekly_messages.find(
        {"chat_id": chat_id, "week": str(start_of_week)}
    ).sort("count", -1).limit(3).to_list(3)
    monthly_top = await db.monthly_messages.find(
        {"chat_id": chat_id, "month": str(start_of_month)}
    ).sort("count", -1).limit(3).to_list(3)
    text = f"**📈 {message.chat.title} Grup İstatistikleri**\n\n"
    text += f"**📅 Günlük (Bugün)**\n"
    text += f"├ Aktif Kullanıcı: {daily_users}\n"
    text += f"├ Toplam Mesaj: {daily_total}\n"
    if daily_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(daily_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except Exception:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{int(user_data.get('count', 0))}`\n"
    text += f"\n**📆 Haftalık (Bu Hafta)**\n"
    text += f"├ Aktif Kullanıcı: {weekly_users}\n"
    text += f"├ Toplam Mesaj: {weekly_total}\n"
    if weekly_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(weekly_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except Exception:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{int(user_data.get('count', 0))}`\n"
    text += f"\n**🗓️ Aylık (Bu Ay)**\n"
    text += f"├ Aktif Kullanıcı: {monthly_users}\n"
    text += f"├ Toplam Mesaj: {monthly_total}\n"
    if monthly_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(monthly_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except Exception:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{int(user_data.get('count', 0))}`\n"
    total_activity = daily_total + weekly_total + monthly_total
    if total_activity > 5000:
        activity_level = "🔥 Çok Yüksek"
    elif total_activity > 2000:
        activity_level = "⚡ Yüksek"
    elif total_activity > 1000:
        activity_level = "✨ Orta"
    elif total_activity > 500:
        activity_level = "💫 Düşük"
    else:
        activity_level = "💤 Çok Düşük"
    text += f"\n**🏆 Genel Aktivite Seviyesi: {activity_level}**"
    await message.reply_text(text)


@app.on_message(filters.command(["skoryardım", "scorehelp"]) & filters.group & ~app.bl_users)
@lang.language()
async def score_help(_, message: types.Message):
    text = "**📊 Mesaj Skor Sistemi Yardım**\n\n"
    text += "**Komutlar:**\n"
    text += "├ `/top` - Günlük sıralama\n"
    text += "├ `/top weekly` - Haftalık sıralama\n"
    text += "├ `/top monthly` - Aylık sıralama\n"
    text += "├ `/mystats` - Kişisel istatistiklerin\n"
    text += "├ `/grupistatistik` - Grup istatistikleri\n"
    text += "└ `/skoryardım` - Bu yardım mesajı\n\n"
    text += "**Sıralama Rozetleri:**\n"
    text += "🥇 **1.** - Altın madalya\n"
    text += "🥈 **2.** - Gümüş madalya\n"
    text += "🥉 **3.** - Bronz madalya\n"
    text += "🏅 **4-5.** - Başarı rozeti\n"
    text += "👤 **6+** - Katılım rozeti\n\n"
    text += "**Aktivite Emojileri:**\n"
    text += "🔥 1000+ mesaj - Aşırı aktif\n"
    text += "⚡ 500+ mesaj - Çok aktif\n"
    text += "✨ 100+ mesaj - Aktif\n"
    text += "💫 50+ mesaj - Orta\n"
    text += "⭐ 10+ mesaj - Az aktif\n"
    text += "💤 10 mesaj - Düşük aktivite\n\n"
    text += "**İpuçları:**\n"
    text += "• Her mesajınız puan kazandırır\n"
    text += "• Günlük, haftalık ve aylık sıralamalar ayrıdır\n"
    text += "• Eski veriler otomatik olarak temizlenir\n"
    text += "• Aktiflik seviyenizi görmek için `/mystats` kullanın"
    await message.reply_text(text)


@app.on_message(filters.command(["testscore"]) & filters.group & ~app.bl_users)
@lang.language()
async def test_score(_, message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    today = datetime.date.today()
    await db.daily_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "date": str(today)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    start_of_week = today - datetime.timedelta(days=today.weekday())
    await db.weekly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "week": str(start_of_week)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    start_of_month = today.replace(day=1)
    await db.monthly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "month": str(start_of_month)},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    daily = await db.daily_messages.find_one(
        {"user_id": user_id, "chat_id": chat_id, "date": str(today)}
    )
    count = int(daily.get("count", 0)) if daily else 0
    await message.reply_text(f"Skor test OK. Bugünkü sayın: {count}")


async def cleanup_old_data():
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)
    await db.daily_messages.delete_many({"date": {"$lt": str(seven_days_ago)}})
    four_weeks_ago = today - datetime.timedelta(weeks=4)
    await db.weekly_messages.delete_many({"week": {"$lt": str(four_weeks_ago)}})
    three_months_ago = today - datetime.timedelta(days=90)
    await db.monthly_messages.delete_many({"month": {"$lt": str(three_months_ago)}})


async def scheduled_cleanup():
    while True:
        await asyncio.sleep(3600)
        try:
            await cleanup_old_data()
        except Exception:
            pass


tasks.append(asyncio.create_task(scheduled_cleanup()))

