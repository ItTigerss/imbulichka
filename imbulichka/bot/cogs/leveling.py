import discord
from discord.ext import commands
from bot.database import db
from config import Config
import math

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def calculate_level(self, xp: int) -> int:
        return int((xp / 100) ** 0.5)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        user_data = db.get_user(message.author.id, message.guild.id)
        if not user_data:
            db.create_user(message.author.id, message.guild.id)
            user_data = db.get_user(message.author.id, message.guild.id)
        
        # Добавляем XP за сообщение
        db.update_xp(message.author.id, message.guild.id, Config.XP_PER_MESSAGE)
        db.update_messages(message.author.id, message.guild.id)
        
        # Проверяем повышение уровня
        user_data = db.get_user(message.author.id, message.guild.id)  # Обновляем данные
        new_xp = user_data['xp']
        new_level = self.calculate_level(new_xp)
        
        if new_level > user_data['level']:
            db.update_level(message.author.id, message.guild.id, new_level)
            
            # Level up message
            if message.channel.permissions_for(message.guild.me).send_messages:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} reached **level {new_level}!**",
                    color=Config.SUCCESS_COLOR
                )
                xp_for_next = int(((new_level + 1) ** 2) * 100)
                embed.add_field(name="XP", value=f"{new_xp}/{xp_for_next}")
                await message.channel.send(embed=embed)
    
    @commands.command(name="rank", aliases=["level", "profile"])
    async def rank_command(self, ctx, member: discord.Member = None):
        """Check your rank and level"""
        member = member or ctx.author
        user_data = db.get_user(member.id, ctx.guild.id)
        
        if not user_data:
            db.create_user(member.id, ctx.guild.id)
            user_data = db.get_user(member.id, ctx.guild.id)
        
        current_level = self.calculate_level(user_data['xp'])
        xp_for_next = int(((current_level + 1) ** 2) * 100)
        xp_current = user_data['xp']
        xp_for_current = int((current_level ** 2) * 100)
        progress = ((xp_current - xp_for_current) / (xp_for_next - xp_for_current)) * 100 if current_level > 0 else 0
        
        embed = discord.Embed(
            title=f"📊 Profile of {member.display_name}",
            color=Config.EMBED_COLOR
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        # Progress bar
        bar_length = 20
        filled = int(bar_length * progress / 100)
        progress_bar = "█" * filled + "░" * (bar_length - filled)
        
        embed.add_field(name="Level", value=f"**{current_level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp_current}/{xp_for_next}**", inline=True)
        embed.add_field(name="Messages", value=f"**{user_data['messages']}**", inline=True)
        embed.add_field(name="Voice Time", value=f"**{user_data['voice_time']} min**", inline=True)
        embed.add_field(name="Coins", value=f"**{user_data['coins']}** ⭐", inline=True)
        embed.add_field(name="Progress", value=f"```{progress_bar} {progress:.1f}%```", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="top", aliases=["leaders", "leaderboard"])
    async def leaderboard_command(self, ctx):
        """Show server leaderboard"""
        top_users = db.get_top_users(ctx.guild.id, 10)
        
        embed = discord.Embed(
            title="🏆 Shineland Leaderboard",
            color=Config.EMBED_COLOR
        )
        
        description = ""
        for i, (user_id, xp, level) in enumerate(top_users, 1):
            user = ctx.guild.get_member(user_id)
            if user:
                medals = ["🥇", "🥈", "🥉"]
                medal = medals[i-1] if i <= 3 else f"{i}."
                description += f"{medal} **{user.display_name}** - Level {level} | {xp} XP\n"
        
        if not description:
            description = "No users found!"
        
        embed.description = description
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))