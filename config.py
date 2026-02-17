from os import getenv
from dotenv import load_dotenv

load_dotenv()


def _env_bool(key: str, default: bool = False) -> bool:
    val = getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}

class Config:
    def __init__(self):
        # Core
        self.API_ID = int(getenv("API_ID", "30527441"))
        self.API_HASH = getenv("API_HASH", "5d5328f4556130c7f5c6055d7a703bc2")
        self.BOT_TOKEN = getenv("BOT_TOKEN", "8284340154:AAH07G9K1e6Lb3LbmTYm9kZj51KlYqVwses")
        self.MONGO_URL = getenv("MONGO_URL", "mongodb+srv://mongoguess:guessmongo@cluster0.zcwklzz.mongodb.net/?retryWrites=true&w=majority") or getenv("MONGO_DB_URI")
        self.LOGGER_ID = int(getenv("LOGGER_ID", "-1003695016820"))
        self.OWNER_ID = int(getenv("OWNER_ID", "8548853828"))
        
        # Sudo Users
        self.SUDO_USERS = {int(x) for x in getenv("SUDO_USERS", "").split()}

        self.OWNER_USERNAME = getenv("OWNER_USERNAME", "@Ekimekadar")
        self.BOT_USERNAME = getenv("BOT_USERNAME", "@AppleSongMusic_Bot")
        self.BOT_NAME = getenv("BOT_NAME", "Apple Musıc")
        self.ASSUSERNAME = getenv("ASSUSERNAME", "@Appppllw")

        # Limits
        self.DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 60))
        self.DURATION_LIMIT = self.DURATION_LIMIT_MIN * 320
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(
            getenv("PLAYLIST_LIMIT", getenv("PLAYLIST_FETCH_LIMIT", 20))
        )
        self.SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "1200"))
        self.SONG_DOWNLOAD_DURATION_LIMIT = int(
            getenv("SONG_DOWNLOAD_DURATION_LIMIT", "1800")
        )
        self.TG_AUDIO_FILESIZE_LIMIT = int(
            getenv("TG_AUDIO_FILESIZE_LIMIT", "157286400")
        )
        self.TG_VIDEO_FILESIZE_LIMIT = int(
            getenv("TG_VIDEO_FILESIZE_LIMIT", "1288490189")
        )

        # Sessions
        self.SESSION1 = getenv("SESSION1", "BQHRz9EAL0B7LILbAUMhAwYt73fseC-7HZ0jvoFCyknm-hfNd2Ck7eGlyzLyO-UlQ1HpI4m9RVaI_U2OjEPffKi4nsZ9MKKgtuqROBJScTggC-f7TUL3XJQrzzXZKuWUFdICRoYQjM0_HiYt1YYenmxierxWQz7rez3xVLu3WCj7fVV6iQYS1xAckp1HA4ySzliC0dhMzxOH2tW8ejr6202qMm8qGgEr2WI82jceI-BX0tHdthtVQkoN48yvktdrKZhhofrD3pDV8JeFyrEDIjBGTcWghvBG9Vg_0164PvRyGlJI4Gpej_e66jVM-hoYZQJPP4q5jLwj94RTHF6KF7P2sB4zcgAAAAG3WPv4AA")
        if not self.SESSION1:
            self.SESSION1 = getenv("SESSION")
        if not self.SESSION1:
            self.SESSION1 = getenv("STRING_SESSION")

        self.SESSION2 = getenv("SESSION2") or getenv("STRING_SESSION2")
        self.SESSION3 = getenv("SESSION3") or getenv("STRING_SESSION3")

        self.STRING4 = getenv("STRING_SESSION4")
        self.STRING5 = getenv("STRING_SESSION5")

        # Support
        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/tr_telegrammarket")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/goygoy_chat")

        # Playback / behavior
        self.AUTO_END = _env_bool("AUTO_END", False)
        self.AUTO_LEAVE = _env_bool("AUTO_LEAVE", False)
        self.VIDEO_PLAY = _env_bool("VIDEO_PLAY", True)
        cookie_env = getenv("COOKIES_URL", "https://batbin.me/grandmothers")
        if not cookie_env:
            cookie_env = getenv("COOKIE_URL", "https://batbin.me/antiphthisical")
        self.COOKIES_URL = [
            url for url in cookie_env.split(" ")
            if url and "batbin.me" in url
        ]
        if not self.COOKIES_URL and cookie_env:
            self.COOKIES_URL = [cookie_env]

        # External APIs
        self.API_URL = getenv("API_URL")
        self.VIDEO_API_URL = getenv("VIDEO_API_URL")
        self.API_KEY = getenv("API_KEY")
        self.DEEP_API = getenv("DEEP_API")

        # Deployment / Git
        self.HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
        self.HEROKU_API_KEY = getenv("HEROKU_API_KEY")
        self.UPSTREAM_REPO = getenv(
            "UPSTREAM_REPO", "https://github.com/CertifiedCoders/AnnieXMusic"
        )
        self.UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "Master")
        self.GIT_TOKEN = getenv("GIT_TOKEN")

        # Integrations
        self.SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
        self.SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")
        self.TMDB_API_KEY = getenv("TMDB_API_KEY", "")

        # Media assets
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://te.legra.ph/file/3e40a408286d4eda24191.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://files.catbox.moe/haagg2.png")
        self.START_IMG = getenv("START_IMG", "https://files.catbox.moe/zvziwk.jpg")
        self.WELCOME_IMG = getenv("WELCOME_IMG", "")
        self.PLAY_ICONS_IMG = getenv(
            "PLAY_ICONS_IMG", "anony/assets/thumb/play_icons.png"
        )
        self.THUMB_FONT = getenv("THUMB_FONT", "anony/assets/thumb/font.ttf")
        self.THUMB_FONT2 = getenv("THUMB_FONT2", "anony/assets/thumb/font2.ttf")

        # Stream quality
        self.AUDIO_QUALITY = getenv("AUDIO_QUALITY", "HIGH")
        self.VIDEO_QUALITY = getenv("VIDEO_QUALITY", "UHD_4K")
        self.STREAM_CACHE = int(getenv("STREAM_CACHE", 200))
        self.FFMPEG_PARAMS = getenv("FFMPEG_PARAMS", "")
        self.STREAM_FFMPEG = getenv(
            "STREAM_FFMPEG",
            "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        )

        # Start media
        self.START_VIDS = [
            "https://files.catbox.moe/a2p7ry.mp4",
            "https://files.catbox.moe/588eop.mp4",
            "https://files.catbox.moe/4rflnn.mp4",
        ]
        self.STICKERS = [
            "CAACAgUAAx0Cld6nKUAACASBI_rna1O1e6g7qS-ry-aZ1ZpVEnwACgg8AAi2LEfFI5wfykOC4h4E",
            "CAACAgUAAx0Cld6nKUAACATJI_rsEJOsaAPSYGhU7bo7iEwL8AAPMDgACu2PYV8Vb8aT4_HUPHgQ",
        ]

        # UI assets
        self.HELP_IMG_URL = getenv("HELP_IMG_URL", "https://files.catbox.moe/yg2vky.jpg")
        self.PING_VID_URL = getenv("PING_VID_URL", "https://files.catbox.moe/3ivvgo.mp4")
        self.PLAYLIST_IMG_URL = getenv("PLAYLIST_IMG_URL", "https://files.catbox.moe/yhaja5.jpg")
        self.STATS_VID_URL = getenv("STATS_VID_URL", "https://telegra.ph/file/e2ab6106ace2e95862372.mp4")
        self.TELEGRAM_AUDIO_URL = getenv("TELEGRAM_AUDIO_URL", "https://files.catbox.moe/mlztag.jpg")
        self.TELEGRAM_VIDEO_URL = getenv("TELEGRAM_VIDEO_URL", "https://files.catbox.moe/tiss2b.jpg")
        self.STREAM_IMG_URL = getenv("STREAM_IMG_URL", "https://files.catbox.moe/1d3da7.jpg")
        self.SOUND_IMG_URL = getenv("SOUND_IMG_URL", "https://files.catbox.moe/zhmxl.jpg")
        self.YOUTUBE_IMG_URL = getenv("YOUTUBE_IMG_URL", "https://files.catbox.moe/yekyxq.jpg")
        self.SPOTIFY_ARTIST_IMG_URL = getenv("SPOTIFY_ARTIST_IMG_URL", self.YOUTUBE_IMG_URL)
        self.SPOTIFY_ALBUM_IMG_URL = getenv("SPOTIFY_ALBUM_IMG_URL", self.YOUTUBE_IMG_URL)
        self.SPOTIFY_PLAYLIST_IMG_URL = getenv("SPOTIFY_PLAYLIST_IMG_URL", self.YOUTUBE_IMG_URL)

        # Emojis
        self.PLAY_EMOJIS = [
            "💞",
            "🦋",
            "🔍",
            "🎤",
            "⚡",
            "🔥",
            "🎩",
            "🌈",
            "🍷",
            "🕺",
            "📱",
            "🕊️",
            "🎉",
            "💌",
            "🧪",
        ]

    def check(self):
        missing = []
        required = ["API_ID", "API_HASH", "BOT_TOKEN", "LOGGER_ID", "OWNER_ID"]
        missing.extend([var for var in required if not getattr(self, var)])
        if not (self.MONGO_URL or getenv("MONGO_DB_URI")):
            missing.append("MONGO_URL")
        if not self.SESSION1:
            missing.append("SESSION1")
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

