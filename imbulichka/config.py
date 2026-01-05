import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Starlight Nexus Theme (Blue/Purple)
COLORS = {
    "PRIMARY": 0x6366F1,      # Индиго
    "SECONDARY": 0x8B5CF6,    # Фиолетовый
    "SUCCESS": 0x10B981,      # Изумрудный
    "ERROR": 0xEF4444,        # Красный
    "WARNING": 0xF59E0B,      # Янтарный
    "INFO": 0x3B82F6,         # Синий
    "DARK": 0x1E1B4B,         # Темно-синий
    "LIGHT": 0xA5B4FC,        # Лавандовый
    "ACCENT": 0x06B6D4,       # Голубой
}

# Emojis
EMOJIS = {
    "COIN": "<:coin:> 💰",
    "CARD": "🃏",
    "XP": "✨",
    "LEVEL": "📈",
    "VOICE": "🎤",
    "MESSAGE": "💬",
    "TIME": "⏱️",
    "RANK": "🏆",
    "STAR": "⭐",
    "GEM": "💎",
    "CHEST": "🎁",
    "VERIFIED": "✅",
    "MODERATION": "🛡️",
    "MUSIC": "🎵",
    "GAME": "🎮",
    "AI": "🤖",
    "UTILITY": "🔧",
}

# Leveling Configuration
LEVEL_CONFIG = {
    "XP_PER_MESSAGE": (15, 25),
    "XP_PER_MINUTE_VOICE": 12,
    "COOLDOWN": 60,
    "BASE_XP": 100,
    "MULTIPLIER": 1.5,
    "LEVELUP_COINS": 100,
}

# Economy Configuration
ECONOMY_CONFIG = {
    "DAILY_BASE": 100,
    "DAILY_STREAK_BONUS": 10,
    "WORK_MIN": 50,
    "WORK_MAX": 200,
    "WORK_COOLDOWN": 3600,
    "CARD_PACK_PRICE": 250,
}

# Card Rarities
CARD_RARITIES = {
    "COMMON": {"chance": 50, "color": 0x94A3B8, "emoji": "⚪", "value": 10},
    "UNCOMMON": {"chance": 25, "color": 0x22C55E, "emoji": "🟢", "value": 25},
    "RARE": {"chance": 15, "color": 0x3B82F6, "emoji": "🔵", "value": 50},
    "EPIC": {"chance": 7, "color": 0x8B5CF6, "emoji": "🟣", "value": 100},
    "LEGENDARY": {"chance": 2.5, "color": 0xF59E0B, "emoji": "🟡", "value": 250},
    "MYTHIC": {"chance": 0.5, "color": 0xEF4444, "emoji": "🔴", "value": 500},
}

# Verification
VERIFICATION_ROLE = "Verified"
MUTE_ROLE = "Muted"
