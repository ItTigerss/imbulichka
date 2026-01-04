import discord
from discord.ext import commands
from bot.database import db
from config import Config
import time

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Игнорируем сообщения ботов и без гильдии
        if message.author.bot or not message.guild:
            return
        
        # Проверяем кулдаун (60 секунд между XP)
        user_id = message.author.id
        current_time = time.time()
        
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < Config.COOLDOWN_SECONDS:
                return
        
        self.cooldowns[user_id] = current_time
        
        # Получаем или создаем пользователя
        user_data = db.get_user(message.author.id, message.guild.id)
        if not user_data:
            db.create_user(message.author.id, message.guild.id)
            user_data = db.get_user(message.author.id, message.guild.id)
        
        # Добавляем XP за сообщение
        import sqlite3
        conn = sqlite3.connect("data/database.db")
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET xp = xp + ?, messages = messages + 1 WHERE user_id = ? AND guild_id = ?",
            (Config.XP_PER_MESSAGE, message.author.id, message.guild.id)
        )
        
        # Проверяем повышение уровня
        cursor.execute(
            "SELECT xp FROM users WHERE user_id = ? AND guild_id = ?",
            (message.author.id, message.guild.id)
        )
        new_xp = cursor.fetchone()[0]
        
        # Вычисляем новый уровень
        new_level = int((new_xp / 100) ** 0.5)
        
        if new_level > user_data['level']:
            cursor.execute(
                "UPDATE users SET level = ? WHERE user_id = ? AND guild_id = ?",
                (new_level, message.author.id, message.guild.id)
            )
            
            # Отправляем сообщение о повышении уровня
            if message.channel.permissions_for(message.guild.me).send_messages:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} reached **level {new_level}!**",
                    color=Config.SUCCESS_COLOR
                )
                await message.channel.send(embed=embed)
        
        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(OnMessage(bot))