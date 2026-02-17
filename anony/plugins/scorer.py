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

