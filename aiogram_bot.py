import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# BOT_TOKEN = "BURAYA_TOKEN_YAZIN"
# Gerçek uygulamada environment variable veya config.py kullanılmalıdır.
TOKEN = getenv("BOT_TOKEN", "7963231435:AAF-7Xo2_v7Z9K9...") # Örnek token yeri

# Router tanımlama
router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    /start komutu geldiğinde özel emoji ve renkli butonlar içeren mesajı gönderir.
    """
    # 1) HTML Formatta Özel Emoji İçeren Mesaj
    # Not: tg-emoji için emoji-id değerini hedef emojiden almalısınız.
    welcome_text = (
        f"Merhaba, <b>{message.from_user.full_name}</b> <tg-emoji emoji-id='5368324170671202286'>✨</tg-emoji>\n\n"
        f"Ben <b>APPLE MUSIC</b> <tg-emoji emoji-id='5368324170671202286'>🎧</tg-emoji>\n\n"
        f"<tg-emoji emoji-id='5368324170671202286'>✨</tg-emoji> Neler yapabilirim?\n"
        f"- 🎵 Grup çağrılarında müzik çalarım\n"
        f"- 🎬 Video oynatırım\n"
        f"- 🌍 Çoklu dil desteği sunarım\n"
        f"- Yönetim komutlarını kullanırım\n"
        f"- 👋 Özel hoşgeldin mesajları\n\n"
        f"<tg-emoji emoji-id='5451893345850763560'>🚀</tg-emoji> Komutlar için aşağıdaki menüyü kullan\n"
        f"💬 Destek: Sertifikalı Kodlayıcı"
    )

    # 2) Inline Keyboard (Renkli ve Özel İkonlu)
    # style='primary' -> Mavi
    # style='success' -> Yeşil
    # style='danger'  -> Kırmızı
    # icon_custom_emoji_id -> Butonun içine özel emoji ekler
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="▶️ Oynat", 
                callback_data="play_music",
                style="success", # Yeşil Buton
                icon_custom_emoji_id="5445271813133181165" # Müzik/Oynat temalı özel emoji ID
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Gruba Ekle", 
                url="https://t.me/your_bot?startgroup=true",
                style="primary", # Mavi Buton
                icon_custom_emoji_id="5451893345850763560"
            )
        ],
        [
            InlineKeyboardButton(
                text="Geliştirici", 
                url="https://t.me/your_username",
                style="success", # Yeşil Buton
                icon_custom_emoji_id="5368324170671202286"
            ),
            InlineKeyboardButton(
                text="Destek", 
                url="https://t.me/your_support",
                style="success", # Yeşil Buton
                icon_custom_emoji_id="5368324170671202286"
            )
        ],
        [
            InlineKeyboardButton(
                text="Yardım & Komutlar", 
                callback_data="help_commands",
                style="danger", # Kırmızı Buton
                icon_custom_emoji_id="5451893345850763560"
            )
        ]
    ])

    # 3) Reply Keyboard (Örnek olarak)
    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🎵 Müzik Çal", style="primary"),
                KeyboardButton(text="⚙️ Ayarlar", style="success")
            ],
            [
                KeyboardButton(text="❌ Durdur", style="danger")
            ]
        ],
        resize_keyboard=True
    )

    # Mesajı gönder
    await message.answer(
        welcome_text,
        reply_markup=inline_kb, # Veya reply_kb kullanabilirsiniz
        parse_mode=ParseMode.HTML
    )

async def main() -> None:
    # Bot nesnesini başlat (HTML parse mode varsayılan olarak da ayarlanabilir)
    bot = Bot(token=TOKEN)
    
    # Dispatcher ve Router kaydı
    dp = Dispatcher()
    dp.include_router(router)

    # Polling başlat
    print("Bot çalışıyor...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
