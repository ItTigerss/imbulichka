import discord
from discord.ext import commands
import asyncio
import aiosqlite
import os
import sys
from datetime import datetime
from config import BOT_TOKEN, COLORS

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found in .env file!")
    sys.exit(1)

print("=" * 50)
print("🚀 Starting Starlight Nexus Bot...")
print("=" * 50)

class StarlightBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db = None
        self.color = COLORS["PRIMARY"]
        self.start_time = datetime.now()
    
    async def setup_hook(self):
        # Initialize database
        os.makedirs("database", exist_ok=True)
        self.db = await aiosqlite.connect("database/starlight.db")
        await self.init_database()
        
        # Load cogs
        cogs = [
            "cogs.menu",
            "cogs.leveling",
            "cogs.economy",
            "cogs.games",
            "cogs.moderation",
            "cogs.utilities",
            "cogs.ai_commands",
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        print(f"✅ Bot ready with {len(self.commands)} commands")
    
    async def init_database(self):
        async with self.db.cursor() as cursor:
            # Users table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    messages INTEGER DEFAULT 0,
                    voice_time INTEGER DEFAULT 0,
                    total_xp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 500,
                    daily_streak INTEGER DEFAULT 0,
                    last_daily TEXT,
                    last_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Cards table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    card_id TEXT,
                    card_name TEXT,
                    rarity TEXT,
                    value INTEGER,
                    obtained_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id, guild_id) REFERENCES users(user_id, guild_id)
                )
            """)
            
            # Warnings table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await self.db.commit()
    
    async def on_ready(self):
        print("=" * 50)
        print(f"🤖 Logged in as: {self.user}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"🌐 Servers: {len(self.guilds)}")
        print(f"⚡ Commands: {len(self.commands)}")
        print("=" * 50)
        
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="✨ Starlight Nexus | !help"
            )
        )
    
    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()

# Create and run bot
bot = StarlightBot()

# Basic ping command
@bot.command(name="ping")
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** {latency}ms",
        color=COLORS["SUCCESS"]
    )
    
    if latency < 100:
        embed.set_footer(text="⚡ Excellent connection!")
    elif latency < 200:
        embed.set_footer(text="✅ Good connection")
    else:
        embed.set_footer(text="⚠️ High latency detected")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n👋 Shutting down bot...")
    except Exception as e:
        print(f"❌ Error: {e}")
