import discord
from discord.ext import commands
import random
from config import COLORS

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="flipcoin", aliases=["coin"])
    async def flipcoin_command(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"**Result:** {result}",
            color=COLORS["WARNING"]
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="8ball")
    async def eightball_command(self, ctx, *, question):
        """Ask the magic 8-ball"""
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt",
            "Yes definitely", "You may rely on it", "As I see it, yes",
            "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again", "Don't count on it",
            "My reply is no", "My sources say no", "Outlook not so good",
            "Very doubtful"
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=0x000000
        )
        
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"**{answer}**", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="rps")
    async def rps_command(self, ctx, choice: str):
        """Rock Paper Scissors"""
        choice = choice.lower()
        choices = ["rock", "paper", "scissors"]
        
        if choice not in choices:
            await ctx.send("Choose: rock, paper, or scissors")
            return
        
        bot_choice = random.choice(choices)
        
        # Determine winner
        if choice == bot_choice:
            result = "🤝 **Tie!**"
            color = COLORS["WARNING"]
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "🎉 **You win!**"
            color = COLORS["SUCCESS"]
        else:
            result = "🤖 **I win!**"
            color = COLORS["ERROR"]
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        embed = discord.Embed(
            title="🪨 📄 ✂️ Rock Paper Scissors",
            color=color
        )
        
        embed.add_field(name="Your Choice", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="My Choice", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="roll", aliases=["dice"])
    async def roll_command(self, ctx, dice: str = "1d6"):
        """Roll dice (format: 2d6)"""
        try:
            if "d" not in dice:
                await ctx.send("Format: `!roll NdM` (ex: 2d6)")
                return
            
            num, sides = map(int, dice.split("d"))
            
            if num > 10:
                num = 10
            if sides > 100:
                sides = 100
            
            rolls = [random.randint(1, sides) for _ in range(num)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                color=COLORS["PRIMARY"]
            )
            
            embed.add_field(name="Command", value=dice, inline=True)
            embed.add_field(name="Results", value=", ".join(map(str, rolls)), inline=True)
            embed.add_field(name="Total", value=str(total), inline=True)
            
            if total == num * sides:
                embed.add_field(name="🎯 Critical!", value="Max roll!", inline=False)
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("Invalid format! Use `!roll NdM`")
    
    @commands.command(name="slots")
    async def slots_command(self, ctx):
        """Play slots"""
        # Check balance
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                "SELECT coins FROM users WHERE user_id = ? AND guild_id = ?",
                (ctx.author.id, ctx.guild.id)
            )
            result = await cursor.fetchone()
            
            if not result or result[0] < 10:
                await ctx.send("You need at least 10 coins to play!")
                return
            
            # Deduct 10 coins
            await cursor.execute(
                "UPDATE users SET coins = coins - 10 WHERE user_id = ? AND guild_id = ?",
                (ctx.author.id, ctx.guild.id)
            )
        
        # Generate slots
        symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "7️⃣", "🔔", "💎"]
        slots = [random.choice(symbols) for _ in range(3)]
        
        # Determine winnings
        if slots[0] == slots[1] == slots[2]:
            if slots[0] == "💎":
                winnings = 500
                result = "💎 **JACKPOT!** 💎"
            else:
                winnings = 100
                result = "🎉 **THREE IN A ROW!**"
        elif slots[0] == slots[1] or slots[1] == slots[2]:
            winnings = 25
            result = "✨ **TWO MATCHING!**"
        else:
            winnings = 0
            result = "😢 **No matches**"
        
        # Add winnings
        if winnings > 0:
            async with self.bot.db.cursor() as cursor:
                await cursor.execute(
                    "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                    (winnings, ctx.author.id, ctx.guild.id)
                )
                await self.bot.db.commit()
        
        # Create embed
        embed = discord.Embed(
            title="🎰 Slot Machine",
            color=COLORS["SECONDARY"]
        )
        
        embed.add_field(
            name="Result",
            value=f"[ {slots[0]} | {slots[1]} | {slots[2]} ]",
            inline=False
        )
        
        embed.add_field(name="Result", value=result, inline=True)
        embed.add_field(name="Winnings", value=f"{winnings} coins", inline=True)
        
        net = winnings - 10
        if net > 0:
            embed.add_field(name="Net Profit", value=f"+{net} coins", inline=True)
            embed.color = COLORS["SUCCESS"]
        else:
            embed.add_field(name="Loss", value=f"-{abs(net)} coins", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="getmeme")
    async def getmeme_command(self, ctx):
        """Get a random meme"""
        memes = [
            "https://i.imgur.com/6VJ4Q8C.png",
            "https://i.imgur.com/8JZJ4Q8.png",
            "https://i.imgur.com/9KJ4Q8C.png",
            "https://i.imgur.com/0LJ4Q8C.png",
        ]
        
        meme_url = random.choice(memes)
        
        embed = discord.Embed(
            title="😂 Random Meme",
            color=COLORS["ACCENT"]
        )
        embed.set_image(url=meme_url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
