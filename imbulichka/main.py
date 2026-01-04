import discord
from discord.ext import commands
from config import Config
import asyncio
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)

class ShinelandBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=Config.PREFIX, intents=intents, help_command=None)
        
    async def setup_hook(self):
        # Загружаем события
        events = [
            'bot.events.on_ready',
            'bot.events.on_message',
            'bot.events.on_voice_state',
            'bot.events.on_member_join'
        ]
        
        for event in events:
            try:
                await self.load_extension(event)
                logging.info(f'Loaded event: {event}')
            except Exception as e:
                logging.error(f'Failed to load event {event}: {e}')
        
        # Загружаем коги
        cogs = [
            'bot.cogs.moderation',
            'bot.cogs.leveling',
            'bot.cogs.games',
            'bot.cogs.cards',
            'bot.cogs.utility',
            'bot.cogs.fun',
            'bot.cogs.ai_chat',
            'bot.cogs.music',
            'bot.cogs.economy'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logging.info(f'Loaded cog: {cog}')
            except Exception as e:
                logging.error(f'Failed to load cog {cog}: {e}')

bot = ShinelandBot()

@bot.command()
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command()
@commands.is_owner()
async def load(ctx, cog: str):
    try:
        await bot.load_extension(f'bot.cogs.{cog}')
        await ctx.send(f'✅ Cog {cog} loaded!')
    except Exception as e:
        await ctx.send(f'❌ Error: {e}')

@bot.command()
@commands.is_owner()
async def reload(ctx, cog: str):
    try:
        await bot.reload_extension(f'bot.cogs.{cog}')
        await ctx.send(f'✅ Cog {cog} reloaded!')
    except Exception as e:
        await ctx.send(f'❌ Error: {e}')

if __name__ == "__main__":
    if not Config.TOKEN or Config.TOKEN == "ваш_токен_бота_здесь":
        print("❌ ERROR: Set DISCORD_TOKEN in .env file!")
        print("❌ Create .env file with: DISCORD_TOKEN=your_token_here")
        exit(1)
    
    bot.run(Config.TOKEN)