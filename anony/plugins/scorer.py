# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import datetime
from pyrogram import filters, types
from anony import app, db, lang

@app.on_message(filters.group & ~app.bl_users)
async def count_message(_, message: types.Message):
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    today = datetime.date.today()
    
    # Daily
    await db.daily_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "date": str(today)},
        {"$inc": {"count": 1}},
        upsert=True
    )

    # Weekly
    start_of_week = today - datetime.timedelta(days=today.weekday())
    await db.weekly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "week": str(start_of_week)},
        {"$inc": {"count": 1}},
        upsert=True
    )

    # Monthly
    start_of_month = today.replace(day=1)
    await db.monthly_messages.update_one(
        {"user_id": user_id, "chat_id": chat_id, "month": str(start_of_month)},
        {"$inc": {"count": 1}},
        upsert=True
    )

@app.on_message(filters.command(["top", "skor"]) & filters.group & ~app.bl_users)
@lang.language()
async def top_users(_, message: types.Message):
    chat_id = message.chat.id
    command = message.command
    period = "daily" 
    if len(command) > 1:
        if command[1] in ["weekly", "haftalık"]:
            period = "weekly"
        elif command[1] in ["monthly", "aylık"]:
            period = "monthly"

    if period == "daily":
        today = datetime.date.today()
        results = db.daily_messages.find({"chat_id": chat_id, "date": str(today)}).sort("count", -1).limit(15)
        period_str = "Günlük"
    elif period == "weekly":
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        results = db.weekly_messages.find({"chat_id": chat_id, "week": str(start_of_week)}).sort("count", -1).limit(15)
        period_str = "Haftalık"
    else: # monthly
        today = datetime.date.today()
        start_of_month = today.replace(day=1)
        results = db.monthly_messages.find({"chat_id": chat_id, "month": str(start_of_month)}).sort("count", -1).limit(15)
        period_str = "Aylık"

    text = f"**📊 {period_str} Mesaj Sıralaması - İlk 15**\n\n"
    total_messages = 0
    total_users = 0
    
    user_list = []
    async for result in results:
        user_id = result["user_id"]
        count = result["count"]
        total_messages += count
        total_users += 1
        
        try:
            user = await app.get_users(user_id)
            username = user.mention
        except:
            username = "Bilinmeyen Kullanıcı"
        
        badge = get_rank_badge(total_users)
        activity_emoji = get_activity_emoji(count)
        
        user_list.append(f"{badge} **{total_users}.** {username}: `{count}` {activity_emoji}")

    if not user_list:
        text += "😴 Henüz kimse mesaj göndermedi."
    else:
        text += "\n".join(user_list)
        text += f"\n\n📈 **Toplam:** {total_messages} mesaj, {total_users} kullanıcı"
        
        # Add some fun statistics
        if total_messages > 0:
            avg_messages = total_messages // total_users
            text += f"\n📊 **Ortalama:** {avg_messages} mesaj/kullanıcı"
            
            if total_messages > 1000:
                text += "\n🎉 **Harika!** Bu grup çok aktif!"
            elif total_messages > 500:
                text += "\n👍 **Güzel!** Grup aktif durumda!"
            elif total_messages > 100:
                text += "\n😊 **İdare eder!** Biraz daha aktiflik gerekir."

@app.on_message(filters.command(["grupistatistik", "groupstats"]) & filters.group & ~app.bl_users)
@lang.language()
async def group_stats(_, message: types.Message):
    chat_id = message.chat.id
    today = datetime.date.today()
    
    # Get daily stats
    today_str = str(today)
    daily_count = await db.daily_messages.count_documents({"chat_id": chat_id, "date": today_str})
    daily_total = await db.daily_messages.aggregate([
        {"$match": {"chat_id": chat_id, "date": today_str}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]).to_list(1)
    daily_total = daily_total[0]["total"] if daily_total else 0
    
    # Get weekly stats
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly_count = await db.weekly_messages.count_documents({"chat_id": chat_id, "week": str(start_of_week)})
    weekly_total = await db.weekly_messages.aggregate([
        {"$match": {"chat_id": chat_id, "week": str(start_of_week)}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]).to_list(1)
    weekly_total = weekly_total[0]["total"] if weekly_total else 0
    
    # Get monthly stats
    start_of_month = today.replace(day=1)
    monthly_count = await db.monthly_messages.count_documents({"chat_id": chat_id, "month": str(start_of_month)})
    monthly_total = await db.monthly_messages.aggregate([
        {"$match": {"chat_id": chat_id, "month": str(start_of_month)}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]).to_list(1)
    monthly_total = monthly_total[0]["total"] if monthly_total else 0
    
    # Get most active users for each period
    daily_top = await db.daily_messages.find({"chat_id": chat_id, "date": today_str}).sort("count", -1).limit(3).to_list(3)
    weekly_top = await db.weekly_messages.find({"chat_id": chat_id, "week": str(start_of_week)}).sort("count", -1).limit(3).to_list(3)
    monthly_top = await db.monthly_messages.find({"chat_id": chat_id, "month": str(start_of_month)}).sort("count", -1).limit(3).to_list(3)
    
    text = f"**📈 {message.chat.title} Grup İstatistikleri**\n\n"
    
    # Daily section
    text += f"**📅 Günlük (Bugün)**\n"
    text += f"├ Aktif Kullanıcı: {daily_count}\n"
    text += f"├ Toplam Mesaj: {daily_total}\n"
    if daily_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(daily_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{user_data['count']}`\n"
    
    # Weekly section
    text += f"\n**📆 Haftalık (Bu Hafta)**\n"
    text += f"├ Aktif Kullanıcı: {weekly_count}\n"
    text += f"├ Toplam Mesaj: {weekly_total}\n"
    if weekly_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(weekly_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{user_data['count']}`\n"
    
    # Monthly section
    text += f"\n**🗓️ Aylık (Bu Ay)**\n"
    text += f"├ Aktif Kullanıcı: {monthly_count}\n"
    text += f"├ Toplam Mesaj: {monthly_total}\n"
    if monthly_top:
        text += "└ En İyi 3:\n"
        for i, user_data in enumerate(monthly_top, 1):
            try:
                user = await app.get_users(user_data["user_id"])
                username = user.mention
            except:
                username = "Bilinmeyen"
            text += f"   {get_rank_badge(i)} {username}: `{user_data['count']}`\n"
    
    # Overall activity level
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
    text = """**📊 Mesaj Skor Sistemi Yardım**\n\n"""
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
    
    text += "**💡 İpuçları:**\n"
    text += "• Her mesajınız puan kazandırır\n"
    text += "• Günlük, haftalık ve aylık sıralamalar ayrıdır\n"
    text += "• Eski veriler otomatik olarak temizlenir\n"
    text += "• Aktiflik seviyenizi görmek için `/mystats` kullanın"
    
    await message.reply_text(text)

@app.on_message(filters.command(["mystats", "benimskor"]) & filters.group & ~app.bl_users)
@lang.language()
async def my_stats(_, message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    today = datetime.date.today()
    
    # Get daily stats
    today_str = str(today)
    daily_result = await db.daily_messages.find_one({"user_id": user_id, "chat_id": chat_id, "date": today_str})
    daily_count = daily_result["count"] if daily_result else 0
    
    # Get weekly stats
    start_of_week = today - datetime.timedelta(days=today.weekday())
    weekly_result = await db.weekly_messages.find_one({"user_id": user_id, "chat_id": chat_id, "week": str(start_of_week)})
    weekly_count = weekly_result["count"] if weekly_result else 0
    
    # Get monthly stats
    start_of_month = today.replace(day=1)
    monthly_result = await db.monthly_messages.find_one({"user_id": user_id, "chat_id": chat_id, "month": str(start_of_month)})
    monthly_count = monthly_result["count"] if monthly_result else 0
    
    # Get rankings
    daily_rank = await get_user_rank(chat_id, "daily", user_id, today_str)
    weekly_rank = await get_user_rank(chat_id, "weekly", user_id, str(start_of_week))
    monthly_rank = await get_user_rank(chat_id, "monthly", user_id, str(start_of_month))
    
    user = message.from_user
    text = f"**{user.mention} - Mesaj İstatistikleri**\n\n"
    text += f"📅 **Günlük:** {daily_count} mesaj"
    if daily_rank > 0:
        text += f" (Sıralama: #{daily_rank})"
    text += f"\n📆 **Haftalık:** {weekly_count} mesaj"
    if weekly_rank > 0:
        text += f" (Sıralama: #{weekly_rank})"
    text += f"\n🗓️ **Aylık:** {monthly_count} mesaj"
    if monthly_rank > 0:
        text += f" (Sıralama: #{monthly_rank})"
    
    # Calculate activity level
    total_messages = daily_count + weekly_count + monthly_count
    if total_messages > 1000:
        level = "🔥 Çok Aktif"
    elif total_messages > 500:
        level = "⚡ Aktif"
    elif total_messages > 100:
        level = "✨ Orta"
    else:
        level = "💤 Az Aktif"
    
    text += f"\n\n🏆 **Aktivite Seviyesi:** {level}"
    
    await message.reply_text(text)

async def get_user_rank(chat_id, period, user_id, period_str):
    if period == "daily":
        pipeline = [
            {"$match": {"chat_id": chat_id, "date": period_str}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}}
        ]
        result = await db.daily_messages.aggregate(pipeline).to_list(1)
    elif period == "weekly":
        pipeline = [
            {"$match": {"chat_id": chat_id, "week": period_str}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}}
        ]
        result = await db.weekly_messages.aggregate(pipeline).to_list(1)
    else: # monthly
        pipeline = [
            {"$match": {"chat_id": chat_id, "month": period_str}},
            {"$sort": {"count": -1}},
            {"$group": {"_id": None, "users": {"$push": "$user_id"}}}
        ]
        result = await db.monthly_messages.aggregate(pipeline).to_list(1)
    
    if result and user_id in result[0]["users"]:
        return result[0]["users"].index(user_id) + 1
    return 0

async def cleanup_old_data():
    """Remove old message data to keep database clean"""
    today = datetime.date.today()
    
    # Clean daily data older than 7 days
    seven_days_ago = today - datetime.timedelta(days=7)
    await db.daily_messages.delete_many({"date": {"$lt": str(seven_days_ago)}})
    
    # Clean weekly data older than 4 weeks
    four_weeks_ago = today - datetime.timedelta(weeks=4)
    await db.weekly_messages.delete_many({"week": {"$lt": str(four_weeks_ago)}})
    
    # Clean monthly data older than 3 months
    three_months_ago = today - datetime.timedelta(days=90)
    await db.monthly_messages.delete_many({"month": {"$lt": str(three_months_ago)}})

# Schedule cleanup task
import asyncio
async def scheduled_cleanup():
    while True:
        await asyncio.sleep(3600)  # Run every hour
        try:
            await cleanup_old_data()
        except Exception as e:
            print(f"Cleanup error: {e}")

# Start cleanup task
import threading
def start_cleanup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduled_cleanup())

# Start cleanup in background
threading.Thread(target=start_cleanup, daemon=True).start()

def get_rank_badge(rank):
    """Get emoji badge for rank"""
    badges = {
        1: "🥇",
        2: "🥈", 
        3: "🥉",
        4: "🏅",
        5: "🏅"
    }
    return badges.get(rank, "👤")

def get_activity_emoji(count):
    """Get activity level emoji"""
    if count > 1000:
        return "🔥"
    elif count > 500:
        return "⚡"
    elif count > 100:
        return "✨"
    elif count > 50:
        return "💫"
    elif count > 10:
        return "⭐"
    else:
        return "💤"


