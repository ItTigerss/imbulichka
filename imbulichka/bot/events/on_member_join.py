import discord
from discord.ext import commands
from config import Config

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != Config.GUILD_ID and Config.GUILD_ID != 0:
            return
        
        # Отправляем приветственное сообщение
        channel = member.guild.system_channel
        if channel:
            embed = discord.Embed(
                title=f"✨ Welcome to {member.guild.name}, {member.name}!",
                description=(
                    f"We're excited to have you here {member.mention}!\n\n"
                    "• Earn XP by chatting and being active\n"
                    "• Collect rare cards with `!pack`\n"
                    "• Play fun games with `!games`\n"
                    "• Level up and climb the leaderboard with `!top`"
                ),
                color=Config.SUCCESS_COLOR
            )
            
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))