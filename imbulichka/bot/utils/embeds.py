import discord
from config import Config

def create_embed(title="", description="", color=None, **kwargs):
    if color is None:
        color = Config.EMBED_COLOR
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        **kwargs
    )
    embed.set_footer(text="Shineland Bot")
    return embed