import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# BOT_TOKEN = "7963231435:AAF-7Xo2_v7Z9K9..." # Kendi token'ınızı buraya ekleyin
TOKEN = getenv("BOT_TOKEN", "7963231435:AAF-7Xo2_v7Z9K9...")

router = Router()

@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    /start komutu ile karşılama mesajı ve renkli butonları gönderir.
    """
    
    # 1) HTML Parse Mode ve Özel Emojili Karşılama Metni
    welcome_text = (
        f"Merhaba, <b>{message.from_user.full_name}</b>\n"
        f"Ben <b>Apple Music</b> <tg-emoji emoji-id='5413491004516834005'>🇹🇷</tg-emoji>/<tg-emoji emoji-id='5415846340334653303'>🇦🇿</tg-emoji>/<tg-emoji emoji-id='5413723337962534575'>�🇸</tg-emoji> 🎧\n\n"
        f"<tg-emoji emoji-id='5368324170671202286'>✨</tg-emoji> Neler yapabilirim?\n"
        f"- 🎵 Grup çağrılarında müzik çalarım\n"
        f"- 🎬 Video oynatırım\n"
        f"- 🌍 Çoklu dil desteği sunarım\n"
        f"- Yönetim komutlarını kullanırım\n"
        f"- 👋 Özel hoşgeldin mesajları\n\n"
        f"<tg-emoji emoji-id='5451893345850763560'>🚀</tg-emoji> Komutlar için aşağıdaki menüyü kullan\n"
        f"💬 Destek: Sertifikalı Kodlayıcı"
    )

    # 2) Renkli Inline Keyboard (style ve icon_custom_emoji_id kullanımı)
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="▶️ Oynat", 
                callback_data="play",
                style="success", # YEŞİL
                icon_custom_emoji_id="5445271813133181165" # Hareketli Müzik İkonu
            )
        ],
        [
            InlineKeyboardButton(
                text="Gruba Ekle", 
                url=f"https://t.me/{message.bot.id}?startgroup=true",
                style="primary", # MAVİ
                icon_custom_emoji_id="5451893345850763560" # Hareketli Grup İkonu
            )
        ],
        [
            InlineKeyboardButton(
                text="Geliştirici", 
                url="https://t.me/your_username",
                style="success", # YEŞİL
                icon_custom_emoji_id="5368324170671202286" # Hareketli Yıldız İkonu
            ),
            InlineKeyboardButton(
                text="Destek", 
                url="https://t.me/your_support",
                style="success", # YEŞİL
                icon_custom_emoji_id="5368324170671202286" # Hareketli Yıldız İkonu
            )
        ],
        [
            InlineKeyboardButton(
                text="Yardım & Komutlar", 
                callback_data="help",
                style="danger", # KIRMIZI
                icon_custom_emoji_id="5451893345850763560" # Hareketli Uyarı İkonu
            )
        ]
    ])

    await message.answer(
        welcome_text,
        reply_markup=inline_kb,
        parse_mode=ParseMode.HTML
    )

async def main() -> None:
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("Bot başlatıldı! /start komutunu göndererek renkli butonları kontrol edin.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

