import discord
from discord.ext import commands
from bot.database import db
from config import Config

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'✅ Logged in as {self.bot.user}')
        print(f'✅ Connected to {len(self.bot.guilds)} guilds')
        
        # База данных уже инициализирована в __init__ класса Database
        print(f'✅ Database initialized at {db.db_path}')
        
        # Set status
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{Config.PREFIX}help | Shineland"
            )
        )

async def setup(bot):
    await bot.add_cog(OnReady(bot))