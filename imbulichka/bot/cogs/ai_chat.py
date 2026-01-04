import discord
from discord.ext import commands
import random
from config import Config

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="chatgpt", aliases=["gpt", "ai"])
    async def ask_ai(self, ctx, *, question):
        """Ask AI a question"""
        responses = [
            f"I think the answer to '{question}' is: Yes, definitely!",
            f"Regarding '{question}', my analysis suggests: Probably not.",
            f"That's an interesting question: {question}. I'd say: It depends on the situation.",
            f"Hmm, '{question}'... Let me think. I believe: The possibilities are endless!",
            f"Based on my calculations for '{question}': The outcome looks positive!",
            f"'{question}'? That's a tough one. I'd suggest: Consider all options carefully.",
            f"Oh, '{question}'! My response is: Absolutely, without a doubt!",
            f"Interesting question about '{question}'. My perspective: Time will tell.",
            f"After processing '{question}', I conclude: The data suggests maybe.",
            f"'{question}'? Let's see... I'd say: Follow your intuition on this."
        ]
        
        embed = discord.Embed(
            title="🤖 AI Assistant",
            description=random.choice(responses),
            color=Config.EMBED_COLOR
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="image", aliases=["generate", "draw"])
    async def generate_image(self, ctx, *, prompt):
        """Generate an image with AI (simulated)"""
        embed = discord.Embed(
            title="🎨 AI Image Generation",
            description=f"**Prompt:** {prompt}\n\n*Image generation would appear here*\n*(Requires OpenAI API key)*",
            color=Config.EMBED_COLOR
        )
        embed.set_footer(text="Enable OpenAI API in .env to generate real images")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIChat(bot))