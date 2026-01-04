import discord
from discord.ext import commands
import random
import sqlite3
from bot.database import db
from config import Config

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="coin", aliases=["flip"])
    async def coin_flip_game(self, ctx, bet: int = 0):
        """Flip a coin with optional bet"""
        user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if bet > 0:
            if user_data['coins'] < bet:
                await ctx.send("You don't have enough coins!")
                return
        
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on... **{result}!**",
            color=Config.EMBED_COLOR
        )
        
        if bet > 0:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            if result == "Heads":
                win_amount = bet * 2
                cursor.execute(
                    "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                    (bet, ctx.author.id, ctx.guild.id)
                )
                embed.add_field(name="Result", value=f"You won **{win_amount}** ⭐!")
            else:
                cursor.execute(
                    "UPDATE users SET coins = coins - ? WHERE user_id = ? AND guild_id = ?",
                    (bet, ctx.author.id, ctx.guild.id)
                )
                embed.add_field(name="Result", value=f"You lost **{bet}** ⭐")
            
            conn.commit()
            conn.close()
        
        await ctx.send(embed=embed)
    
    @commands.command(name="dice")
    async def dice_roll_game(self, ctx, bet: int = 0):
        user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if bet > 0 and user_data['coins'] < bet:
            await ctx.send("You don't have enough coins!")
            return
        
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        total = roll1 + roll2
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled **{roll1}** and **{roll2}**\nTotal: **{total}**",
            color=Config.EMBED_COLOR
        )
        
        if bet > 0:
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            if total >= 7:
                win_amount = int(bet * 1.5)
                cursor.execute(
                    "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                    (win_amount, ctx.author.id, ctx.guild.id)
                )
                embed.add_field(name="Result", value=f"You won **{win_amount}** ⭐!")
            else:
                cursor.execute(
                    "UPDATE users SET coins = coins - ? WHERE user_id = ? AND guild_id = ?",
                    (bet, ctx.author.id, ctx.guild.id)
                )
                embed.add_field(name="Result", value=f"You lost **{bet}** ⭐")
            
            conn.commit()
            conn.close()
        
        await ctx.send(embed=embed)
    
    @commands.command(name="slots")
    async def slots_command(self, ctx, bet: int = 10):
        """Play slots"""
        user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if user_data['coins'] < bet:
            await ctx.send("You don't have enough coins!")
            return
        
        # Subtract bet
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ? AND guild_id = ?",
            (bet, ctx.author.id, ctx.guild.id)
        )
        
        symbols = ["🍒", "🍋", "🍊", "⭐", "🔔", "7️⃣"]
        slots = [random.choice(symbols) for _ in range(3)]
        
        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"**[ {slots[0]} | {slots[1]} | {slots[2]} ]**",
            color=Config.EMBED_COLOR
        )
        
        # Check win
        if slots[0] == slots[1] == slots[2]:
            win_amount = bet * 10
            result = "JACKPOT! 🎉"
        elif slots[0] == slots[1] or slots[1] == slots[2]:
            win_amount = bet * 2
            result = "Two in a row!"
        else:
            win_amount = 0
            result = "No win"
        
        if win_amount > 0:
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                (win_amount, ctx.author.id, ctx.guild.id)
            )
            embed.add_field(name="Result", value=f"{result}\nYou won **{win_amount}** ⭐!")
        else:
            embed.add_field(name="Result", value="Better luck next time!")
        
        conn.commit()
        conn.close()
        
        embed.set_footer(text=f"Balance: {user_data['coins'] + win_amount - bet} ⭐")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Games(bot))