import discord
from discord.ext import commands
import random
from config import Config

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="help")
    async def custom_help(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="🌟 Shineland Bot Help",
            description="**List of ALL available commands:**\n*Prefix: `!`*",
            color=Config.EMBED_COLOR
        )
        
        # ECONOMY
        embed.add_field(
            name="💰 **Economy**",
            value="• `!work` / `!job` - Work for coins (5 min cooldown)\n"
                  "• `!daily` - Daily reward (100-500 coins)\n"
                  "• `!balance` / `!bal` / `!coins` - Check your coins\n"
                  "• `!give @user amount` - Give coins to someone",
            inline=False
        )
        
        # CARDS
        embed.add_field(
            name="🃏 **Cards**",
            value="• `!card` / `!getcard` - Find free card (2 hour cooldown)\n"
                  "• `!pack` / `!buycard` - Buy card pack (1000 coins)\n"
                  "• `!collection` / `!cards` - View your cards",
            inline=False
        )
        
        # LEVELING
        embed.add_field(
            name="📊 **Leveling**",
            value="• `!rank` / `!level` / `!profile` - Check your rank\n"
                  "• `!top` / `!leaders` / `!leaderboard` - Server leaderboard\n"
                  "• *XP earned by: chatting, voice activity, time on server*",
            inline=False
        )
        
        # FUN
        embed.add_field(
            name="🎮 **Fun & Games**",
            value="• `!coinflip` / `!cf` / `!toss` - Flip a coin\n"
                  "• `!8ball <question>` / `!ask` / `!magic` - Ask magic 8-ball\n"
                  "• `!diceroll XdY` / `!dr` - Roll dice (e.g., !dr 2d6)\n"
                  "• `!coin <bet>` - Coin flip with bet\n"
                  "• `!dice <bet>` - Dice game with bet\n"
                  "• `!slots <bet>` - Play slot machine",
            inline=False
        )
        
        # MODERATION
        embed.add_field(
            name="🛡️ **Moderation**",
            value="• `!clear <amount>` / `!purge` - Clear messages\n"
                  "• `!kick @user <reason>` - Kick user\n"
                  "• `!ban @user <reason>` - Ban user\n"
                  "• `!mute @user <minutes> <reason>` - Mute user\n"
                  "*Requires appropriate permissions*",
            inline=False
        )
        
        # AI & UTILITY
        embed.add_field(
            name="🤖 **AI & Utility**",
            value="• `!chatgpt <question>` / `!gpt` / `!ai` - Ask AI\n"
                  "• `!image <prompt>` / `!generate` / `!draw` - Generate image\n"
                  "• `!userinfo @user` / `!ui` - User information\n"
                  "• `!serverinfo` / `!si` - Server information\n"
                  "• `!ping` - Check bot latency",
            inline=False
        )
        
        # MUSIC
        embed.add_field(
            name="🎵 **Music**",
            value="• `!join` - Join voice channel\n"
                  "• `!leave` - Leave voice channel",
            inline=False
        )
        
        embed.set_footer(text=f"Total commands: {len(self.bot.commands)} | Bot: {self.bot.user.name}")
        await ctx.send(embed=embed)
    
    @commands.command(name="userinfo", aliases=["ui"])
    async def user_info(self, ctx, member: discord.Member = None):
        """Show user information"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"👤 User Info: {member.display_name}",
            color=member.color or Config.EMBED_COLOR
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Discord Join", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Server Join", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Bot", value="✅" if member.bot else "❌", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo", aliases=["si"])
    async def server_info(self, ctx):
        """Show server information"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"🏰 Server Info: {guild.name}",
            color=Config.EMBED_COLOR
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Boost Tier", value=guild.premium_tier, inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))