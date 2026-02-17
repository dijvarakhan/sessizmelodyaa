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

    text = f"**Grubunuzda {period_str} en çok aktif olan 15 kişi:**\n\n"
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
            user_list.append(f"**{total_users}.** {user.mention}: {count}")
        except:
            user_list.append(f"**{total_users}.** Bilinmeyen Kullanıcı: {count}")

    if not user_list:
        text += "Henüz kimse mesaj göndermedi."
    else:
        text += "\n".join(user_list)
        text += f"\n\nToplam mesaj: {total_messages}"
        text += f"\nToplam kullanıcı: {total_users}"

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

