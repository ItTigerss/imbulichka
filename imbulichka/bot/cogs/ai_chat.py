import discord
from discord.ext import commands
import random
from config import COLORS

class AICommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="ask")
    async def ask_command(self, ctx, *, question):
        """Ask AI a question"""
        responses = [
            "That's an interesting question! I believe the answer is yes.",
            "Based on my analysis, I would say no.",
            "It depends on the context, but generally yes.",
            "I'm not entirely sure about that one.",
            "According to my knowledge base, the answer is affirmative.",
            "That's a tricky question. Let me think... Probably not.",
            "Yes, definitely!",
            "No, I don't think so.",
            "Maybe, it's hard to say for certain.",
            "I need more information to answer that properly.",
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="🤖 AI Response",
            color=COLORS["ACCENT"]
        )
        
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        
        embed.set_footer(text="AI responses are simulated")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="image")
    async def image_command(self, ctx, *, prompt):
        """Generate an image"""
        image_urls = [
            "https://i.imgur.com/6VJ4Q8C.png",
            "https://i.imgur.com/8JZJ4Q8.png",
            "https://i.imgur.com/9KJ4Q8C.png",
            "https://i.imgur.com/0LJ4Q8C.png",
        ]
        
        image_url = random.choice(image_urls)
        
        embed = discord.Embed(
            title="🎨 Generated Image",
            color=COLORS["SECONDARY"]
        )
        
        embed.add_field(name="Prompt", value=prompt, inline=False)
        embed.set_image(url=image_url)
        
        embed.set_footer(text="AI image generation is simulated")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="translate")
    async def translate_command(self, ctx, lang: str = "en", *, text: str):
        """Translate text"""
        languages = {
            "en": "English",
            "ru": "Russian",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
        }
        
        if lang not in languages:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Language '{lang}' not supported.\nAvailable: {', '.join(languages.keys())}",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
            return
        
        # Mock translation
        translated = f"[{languages[lang]}] {text} (translated)"
        
        embed = discord.Embed(
            title="🌐 Translation",
            color=COLORS["INFO"]
        )
        
        embed.add_field(name="Original", value=text, inline=False)
        embed.add_field(name=f"Translated to {languages[lang]}", value=translated, inline=False)
        
        embed.set_footer(text="Translation is simulated")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="summarize")
    async def summarize_command(self, ctx, *, text: str):
        """Summarize text"""
        if len(text) < 50:
            summary = text
        else:
            summary = text[:100] + "... [summarized]"
        
        embed = discord.Embed(
            title="📝 Summary",
            color=COLORS["PRIMARY"]
        )
        
        embed.add_field(name="Original", value=text[:500] + ("..." if len(text) > 500 else ""), inline=False)
        embed.add_field(name="Summary", value=summary, inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AICommandsCog(bot))
