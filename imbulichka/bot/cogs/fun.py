import discord
from discord.ext import commands
import random
from config import Config

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="8ball", aliases=["ask", "magic"])
    async def eight_ball(self, ctx, *, question):
        """Ask the magic 8-ball a question"""
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.",
            "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.", "Outlook not so good.",
            "Very doubtful."
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"Question: {question}\nAnswer: {random.choice(responses)}",
            color=Config.EMBED_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="coinflip", aliases=["cf", "toss"])
    async def coin_flip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=Config.EMBED_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="diceroll", aliases=["dr"])
    async def dice_roll_fun(self, ctx, dice: str = "1d6"):
        """Roll dice (format: XdY) - Fun version"""
        try:
            num, sides = map(int, dice.split('d'))
            if num > 20 or sides > 100:
                await ctx.send("Maximum is 20d100!")
                return
            
            rolls = [random.randint(1, sides) for _ in range(num)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll",
                description=f"Rolling {dice}...",
                color=Config.EMBED_COLOR
            )
            embed.add_field(name="Rolls", value=str(rolls)[1:-1], inline=False)
            embed.add_field(name="Total", value=str(total), inline=True)
            await ctx.send(embed=embed)
            
        except:
            await ctx.send("Format: !diceroll XdY (e.g., !diceroll 2d6)")

async def setup(bot):
    await bot.add_cog(Fun(bot))