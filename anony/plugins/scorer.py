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
