import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("DISCORD_TOKEN", "")
    PREFIX = os.getenv("BOT_PREFIX", "!")
    GUILD_ID = int(os.getenv("GUILD_ID", 0))
    
    # Leveling settings
    XP_PER_MESSAGE = 15
    XP_PER_MINUTE_VOICE = 10
    XP_PER_HOUR_SERVER = 5
    COOLDOWN_SECONDS = 60
    
    # Card game
    CARD_PACK_PRICE = 1000
    
    # Colors
    EMBED_COLOR = 0x9B59B6
    SUCCESS_COLOR = 0x2ECC71
    ERROR_COLOR = 0xE74C3C
    WARNING_COLOR = 0xF1C40F