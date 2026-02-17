import asyncio
import datetime
from pyrogram import filters, types
from anony import app, db, lang, tasks


@app.on_message(filters.group & ~app.bl_users)
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


def get_rank_badge(rank: int) -> str:
    badges = {1: "🥇", 2: "🥈", 3: "🥉", 4: "🏅", 5: "🏅"}
    return badges.get(rank, "👤")


def get_activity_emoji(count: int) -> str:
    if count > 1000:
        return "🔥"
    if count > 500:
        return "⚡"
    if count > 100:
        return "✨"
    if count > 50:
        return "💫"
    if count > 10:
        return "⭐"
    return "💤"


async def get_leaderboard_text(chat_id: int, period: str) -> str:
    if period == "daily":
        today = datetime.date.today()
        results = (
            db.daily_messages.find({"chat_id": chat_id, "date": str(today)})
            .sort("count", -1)
            .limit(15)
        )
        period_str = "Günlük"
    elif period == "weekly":
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        results = (
            db.weekly_messages.find({"chat_id": chat_id, "week": str(start_of_week)})
            .sort("count", -1)
            .limit(15)
        )
        period_str = "Haftalık"
    elif period == "monthly":
        today = datetime.date.today()
        start_of_month = today.replace(day=1)
        results = (
            db.monthly_messages.find({"chat_id": chat_id, "month": str(start_of_month)})
            .sort("count", -1)
            .limit(15)
        )
        period_str = "Aylık"
    elif period == "alltime":
        results = (
            db.all_time_messages.find({"chat_id": chat_id})
            .sort("count", -1)
            .limit(15)
        )
        period_str = "Tüm Zamanlar"
    else:
        return "Geçersiz süre."

    text = f"**📊 {period_str} Mesaj Sıralaması - İlk 15**\n\n"
    total_messages = 0
    total_users = 0
    user_list = []
    async for result in results:
        user_id = result.get("user_id")
        count = int(result.get("count", 0))
        total_messages += count
        total_users += 1
        try:
            user = await app.get_users(user_id)
            username = user.mention
        except Exception:
            username = "Bilinmeyen Kullanıcı"
        badge = get_rank_badge(total_users)
        activity_emoji = get_activity_emoji(count)
        user_list.append(f"{badge} **{total_users}.** {username}: `{count}` {activity_emoji}")
    
    if not user_list:
        text += "😴 Henüz kimse mesaj göndermedi."
    else:
        text += "\n".join(user_list)
        text += f"\n\n📈 **Toplam:** {total_messages} mesaj, {total_users} kullanıcı"
        if total_messages > 0 and total_users > 0:
            avg_messages = total_messages // total_users
            text += f"\n📊 **Ortalama:** {avg_messages} mesaj/kullanıcı"
            if total_messages > 1000:
                text += "\n🎉 **Harika!** Bu grup çok aktif!"
            elif total_messages > 500:
                text += "\n👍 **Güzel!** Grup aktif durumda!"
            elif total_messages > 100:
                text += "\n😊 **İdare eder!** Biraz daha aktiflik gerekir."
    return text


@app.on_message(filters.command(["top", "skor"]) & filters.group & ~app.bl_users)
@lang.language()
async def top_users(_, message: types.Message):
    cmd = message.command
    if len(cmd) > 1:
        # If user explicitly asks for /top weekly, show it directly?
        # But the request is to show the menu. I'll stick to the menu unless they insist.
        # Actually, for backward compatibility, if they type /top weekly, showing weekly stats directly is better UX.
        # But if just /top, show menu.
        arg = cmd[1].lower()
        if arg in ["weekly", "haftalık"]:
            text = await get_leaderboard_text(message.chat.id, "weekly")
            await message.reply_text(text)
            return
        elif arg in ["monthly", "aylık"]:
            text = await get_leaderboard_text(message.chat.id, "monthly")
            await message.reply_text(text)
            return

    # Show menu
    user_mention = message.from_user.mention if message.from_user else "Anonim"
    text = "👥 Bulunduğunuz grup için sıralama türünü seçiniz.\n\n"
    text += "🖼 Görsel sıralama için `/topbilgi` komutunu kullanınız. ❞\n\n"
    text += f"Bu menü {user_mention} Tarafından açıldı."
    
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("📆 Günlük", callback_data="top_daily"),
                types.InlineKeyboardButton("📆 Haftalık", callback_data="top_weekly"),
                types.InlineKeyboardButton("📆 Aylık", callback_data="top_monthly"),
            ],
            [
                types.InlineKeyboardButton("📊 Bütün zamanlarda", callback_data="top_alltime"),
            ],
            [
                types.InlineKeyboardButton("📄 Detaylı bilgi", callback_data="score_help_cb"),
                types.InlineKeyboardButton("🌐 Global Gruplar", callback_data="global_stats"),
            ],
        ]
    )
    await message.reply_text(text, reply_markup=markup)


@app.on_callback_query(filters.regex(r"^top_") & ~app.bl_users)
async def top_callback(_, query: types.CallbackQuery):
    period_map = {
        "top_daily": "daily",
        "top_weekly": "weekly",
        "top_monthly": "monthly",
        "top_alltime": "alltime",
    }
    period = period_map.get(query.data)
    if not period:
        return
    
    text = await get_leaderboard_text(query.message.chat.id, period)
    
    # Keep the buttons so user can switch tabs
    markup = query.message.reply_markup
    
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except Exception:
        # Message not modified
        pass


@app.on_callback_query(filters.regex("score_help_cb") & ~app.bl_users)
async def help_callback(_, query: types.CallbackQuery):
    # Show help text, maybe with a back button to the menu?
    # Or just edit text to help.
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
    text += "💤 10 mesaj - Düşük aktivite\n"

    # Add back button
    markup = types.InlineKeyboardMarkup(
        [
            [types.InlineKeyboardButton("🔙 Geri Dön", callback_data="top_back")]
        ]
    )
    await query.edit_message_text(text, reply_markup=markup)


@app.on_callback_query(filters.regex("top_back") & ~app.bl_users)
async def back_callback(_, query: types.CallbackQuery):
    # Restore main menu
    user_mention = query.from_user.mention if query.from_user else "Anonim"
    text = "👥 Bulunduğunuz grup için sıralama türünü seçiniz.\n\n"
    text += "🖼 Görsel sıralama için `/topbilgi` komutunu kullanınız. ❞\n\n"
    # Note: Using the callback user might differ from original opener, but it's acceptable.
    # Ideally we preserve the original text, but recreating it is fine.
    text += f"Bu menü {user_mention} Tarafından açıldı."
    
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("📆 Günlük", callback_data="top_daily"),
                types.InlineKeyboardButton("📆 Haftalık", callback_data="top_weekly"),
                types.InlineKeyboardButton("📆 Aylık", callback_data="top_monthly"),
            ],
            [
                types.InlineKeyboardButton("📊 Bütün zamanlarda", callback_data="top_alltime"),
            ],
            [
                types.InlineKeyboardButton("📄 Detaylı bilgi", callback_data="score_help_cb"),
                types.InlineKeyboardButton("🌐 Global Gruplar", callback_data="global_stats"),
            ],
        ]
    )
    await query.edit_message_text(text, reply_markup=markup)


@app.on_callback_query(filters.regex("global_stats") & ~app.bl_users)
async def global_stats_callback(_, query: types.CallbackQuery):
    await query.answer("🌐 Global istatistikler henüz aktif değil!", show_alert=True)


async def get_user_rank(chat_id: int, period: str, user_id: int, key: str) -> int:
    if period == "daily":
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": key}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}},
        ]
        result = await db.daily_messages.aggregate(pipeline).to_list(1)
    elif period == "weekly":
        pipeline = [
            {"$match": {"chat_id": chat_id, "week": key}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}},
        ]
        result = await db.weekly_messages.aggregate(pipeline).to_list(1)
    else:
        pipeline = [
            {"$match": {"chat_id": chat_id, "month": key}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}},
        ]
        result = await db.monthly_messages.aggregate(pipeline).to_list(1)
    if result and user_id in result[0].get("users", []):
        return result[0]["users"].index(user_id) + 1
    return 0


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


