import discord
from discord.ext import commands
import time
from bot.database import db
from config import Config

class OnVoiceState(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_times = {}
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        
        guild = member.guild
        
        # Пользователь зашел в войс
        if before.channel is None and after.channel is not None:
            self.voice_times[member.id] = time.time()
            print(f"{member} joined voice channel {after.channel.name}")
        
        # Пользователь вышел из войса
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_times:
                time_spent = time.time() - self.voice_times[member.id]
                minutes = int(time_spent / 60)
                
                if minutes >= 1:
                    # Добавляем XP за время в войсе
                    xp_to_add = minutes * Config.XP_PER_MINUTE_VOICE
                    
                    import sqlite3
                    conn = sqlite3.connect("data/database.db")
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        "UPDATE users SET xp = xp + ?, voice_time = voice_time + ? WHERE user_id = ? AND guild_id = ?",
                        (xp_to_add, minutes, member.id, guild.id)
                    )
                    
                    conn.commit()
                    conn.close()
                    
                    print(f"{member} earned {xp_to_add} XP for {minutes} minutes in voice")
                
                del self.voice_times[member.id]

async def setup(bot):
    await bot.add_cog(OnVoiceState(bot))