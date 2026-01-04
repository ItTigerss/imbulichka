import discord
from discord.ext import commands
import random
import sqlite3
from datetime import datetime, timedelta
from bot.database import db
from config import Config

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.daily_cooldowns = {}
    
    @commands.command(name="work", aliases=["job"])
    async def work_command(self, ctx):
        """Work to earn coins (5 min cooldown)"""
        user_id = ctx.author.id
        current_time = datetime.now()
        
        # Проверка кулдауна (5 минут)
        if user_id in self.cooldowns:
            time_passed = current_time - self.cooldowns[user_id]
            if time_passed < timedelta(minutes=5):
                remaining = timedelta(minutes=5) - time_passed
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)
                await ctx.send(f"⏰ You need to wait {minutes}m {seconds}s before working again!")
                return
        
        # Начисляем монеты
        earnings = random.randint(50, 200)
        
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
            (earnings, ctx.author.id, ctx.guild.id)
        )
        
        conn.commit()
        conn.close()
        
        # Устанавливаем кулдаун
        self.cooldowns[user_id] = current_time
        
        embed = discord.Embed(
            title="💰 Work Completed!",
            description=f"{ctx.author.mention} earned **{earnings}** ⭐!",
            color=Config.SUCCESS_COLOR
        )
        embed.add_field(name="Next work", value="Available in 5 minutes")
        await ctx.send(embed=embed)
    
    @commands.command(name="daily")
    async def daily_reward(self, ctx):
        """Claim daily reward"""
        user_id = ctx.author.id
        current_time = datetime.now()
        
        # Проверка кулдауна (24 часа)
        if user_id in self.daily_cooldowns:
            time_passed = current_time - self.daily_cooldowns[user_id]
            if time_passed < timedelta(hours=24):
                remaining = timedelta(hours=24) - time_passed
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await ctx.send(f"⏰ Come back in {hours}h {minutes}m for your next daily reward!")
                return
        
        reward = random.randint(100, 500)
        
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
            (reward, ctx.author.id, ctx.guild.id)
        )
        
        conn.commit()
        conn.close()
        
        # Устанавливаем кулдаун
        self.daily_cooldowns[user_id] = current_time
        
        embed = discord.Embed(
            title="🎁 Daily Reward!",
            description=f"{ctx.author.mention} claimed daily reward: **{reward}** ⭐!",
            color=Config.SUCCESS_COLOR
        )
        embed.set_footer(text="Come back tomorrow for more!")
        await ctx.send(embed=embed)
    
    @commands.command(name="balance", aliases=["bal", "coins"])
    async def check_balance(self, ctx, member: discord.Member = None):
        """Check your coin balance"""
        member = member or ctx.author
        
        user_data = db.get_user(member.id, ctx.guild.id)
        if not user_data:
            db.create_user(member.id, ctx.guild.id)
            user_data = db.get_user(member.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"💰 {member.display_name}'s Balance",
            description=f"**{user_data['coins']}** ⭐",
            color=Config.EMBED_COLOR
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="give")
    async def give_coins(self, ctx, member: discord.Member, amount: int):
        """Give coins to another user"""
        if amount <= 0:
            await ctx.send("Amount must be positive!")
            return
        
        if member == ctx.author:
            await ctx.send("You can't give coins to yourself!")
            return
        
        sender_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if not sender_data or sender_data['coins'] < amount:
            await ctx.send("You don't have enough coins!")
            return
        
        receiver_data = db.get_user(member.id, ctx.guild.id)
        if not receiver_data:
            db.create_user(member.id, ctx.guild.id)
        
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Снимаем у отправителя
        cursor.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ? AND guild_id = ?",
            (amount, ctx.author.id, ctx.guild.id)
        )
        
        # Даем получателю
        cursor.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
            (amount, member.id, ctx.guild.id)
        )
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="💰 Transfer Complete",
            description=f"{ctx.author.mention} gave **{amount}** ⭐ to {member.mention}!",
            color=Config.SUCCESS_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))