import discord
from discord.ext import commands
from config import Config

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="join")
    async def join_voice(self, ctx):
        """Join voice channel"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"✅ Joined {channel.name}")
        else:
            await ctx.send("❌ You need to be in a voice channel!")
    
    @commands.command(name="leave")
    async def leave_voice(self, ctx):
        """Leave voice channel"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("✅ Left voice channel")
        else:
            await ctx.send("❌ I'm not in a voice channel!")

async def setup(bot):
    await bot.add_cog(Music(bot))