import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta
import random
import math
from enum import Enum

# Настройки бота
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Файлы для хранения данных
DATA_FILE = "data.json"
CONFIG_FILE = "config.json"

# Тематика Winx Club
class WinxFairy(Enum):
    BLOOM = {"name": "🔥 Блум", "color": discord.Color.red(), "emoji": "🔥"}
    STELLA = {"name": "✨ Стелла", "color": discord.Color.gold(), "emoji": "✨"}
    FLORA = {"name": "🌿 Флора", "color": discord.Color.green(), "emoji": "🌿"}
    MUSHA = {"name": "💧 Муза", "color": discord.Color.blue(), "emoji": "💧"}
    TECNA = {"name": "⚡ Текна", "color": discord.Color.purple(), "emoji": "⚡"}
    LAYLA = {"name": "💎 Лейла", "color": discord.Color.teal(), "emoji": "💎"}

# Уровни феечек Winx
WINX_LEVELS = {
    1: {"name": "😇 Обычная фея", "xp_required": 0},
    5: {"name": "🌟 Фея Чармикс", "xp_required": 500},
    10: {"name": "💫 Фея Энчантикс", "xp_required": 1500},
    15: {"name": "✨ Фея Белэвикс", "xp_required": 3000},
    20: {"name": "🌸 Фея Созикс", "xp_required": 5000},
    25: {"name": "🌙 Фея Хармоникс", "xp_required": 8000},
    30: {"name": "👑 Королева фей", "xp_required": 12000},
    35: {"name": "💖 Хранительница Дракона", "xp_required": 17000},
    40: {"name": "🦋 Фея Баттерфликс", "xp_required": 23000},
    50: {"name": "🌌 Легендарная фея", "xp_required": 35000}
}

# Загрузка данных
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "warns": {}, "voice_sessions": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_config():
    default_config = {
        "xp_per_message": 5,
        "xp_cooldown": 60,
        "xp_per_minute_voice": 2,
        "bonus_xp_activity": 10,
        "level_multiplier": 100,
        "admin_roles": ["Администратор", "Модератор"],
        "mute_role": "Muted",
        "log_channel": None,
        "voice_xp_interval": 60,  # секунды между начислением XP в войсе
        "daily_bonus": 50,
        "streak_bonus": 25,
        "quest_channel": None
    }
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    except FileNotFoundError:
        return default_config

# Инициализация
data = load_data()
config = load_config()

# Система квестов
QUESTS = {
    "daily_messages": {
        "name": "📝 Ежедневные сообщения",
        "description": "Написать 10 сообщений за день",
        "goal": 10,
        "reward": 100,
        "type": "messages"
    },
    "voice_explorer": {
        "name": "🎤 Исследователь голосовых",
        "description": "Провести 30 минут в голосовом канале",
        "goal": 30,
        "reward": 150,
        "type": "voice_minutes"
    },
    "active_member": {
        "name": "⭐ Активный участник",
        "description": "Быть активным 5 дней подряд",
        "goal": 5,
        "reward": 200,
        "type": "streak"
    },
    "helper": {
        "name": "🤝 Помощник",
        "description": "Помочь 3 раза новым участникам",
        "goal": 3,
        "reward": 120,
        "type": "help"
    }
}

class UserManager:
    @staticmethod
    def get_user_data(user_id):
        user_id = str(user_id)
        if user_id not in data["users"]:
            today = datetime.now().strftime("%Y-%m-%d")
            data["users"][user_id] = {
                "xp": 0,
                "level": 1,
                "messages": 0,
                "voice_minutes": 0,
                "last_message": 0,
                "last_daily": None,
                "daily_streak": 0,
                "fairy_type": None,
                "quests": {},
                "achievements": [],
                "total_xp": 0,
                "join_date": datetime.now().isoformat(),
                "warns": 0,
                "today_messages": 0,
                "today_voice": 0,
                "help_counter": 0
            }
        return data["users"][user_id]

    @staticmethod
    def add_xp(user_id, xp_amount, source="message"):
        user = UserManager.get_user_data(user_id)
        user["xp"] += xp_amount
        user["total_xp"] += xp_amount
        
        # Обновляем счетчики для квестов
        if source == "message":
            user["today_messages"] += 1
        elif source == "voice":
            user["today_voice"] += (xp_amount / config["xp_per_minute_voice"]) * 60  # в секундах
        
        # Проверка квестов
        UserManager.check_quests(user_id, source)
        
        old_level = user["level"]
        new_level = UserManager.calculate_level(user["total_xp"])
        
        if new_level > old_level:
            user["level"] = new_level
            save_data(data)
            return {"leveled_up": True, "old_level": old_level, "new_level": new_level}
        
        save_data(data)
        return {"leveled_up": False}

    @staticmethod
    def calculate_level(total_xp):
        level = 1
        xp_needed = 0
        
        while True:
            xp_needed += level * config["level_multiplier"]
            if total_xp >= xp_needed:
                level += 1
            else:
                break
        
        return min(level, 100)  # Максимальный уровень 100

    @staticmethod
    def get_fairy_type(user_id):
        user = UserManager.get_user_data(user_id)
        if not user["fairy_type"]:
            # Автоматически определяем тип феи по активности
            fairy_types = list(WinxFairy)
            user["fairy_type"] = random.choice(fairy_types).name
            save_data(data)
        return WinxFairy[user["fairy_type"]]

    @staticmethod
    def set_fairy_type(user_id, fairy_name):
        try:
            fairy = WinxFairy[fairy_name.upper()]
            user = UserManager.get_user_data(user_id)
            user["fairy_type"] = fairy.name
            save_data(data)
            return True
        except KeyError:
            return False

    @staticmethod
    def get_winx_level(level):
        for lvl in sorted(WINX_LEVELS.keys(), reverse=True):
            if level >= lvl:
                return WINX_LEVELS[lvl]
        return WINX_LEVELS[1]

    @staticmethod
    def check_quests(user_id, quest_type):
        user = UserManager.get_user_data(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        for quest_id, quest in QUESTS.items():
            if quest["type"] == quest_type:
                if quest_id not in user["quests"]:
                    user["quests"][quest_id] = {"progress": 0, "completed": False}
                
                if not user["quests"][quest_id]["completed"]:
                    user["quests"][quest_id]["progress"] += 1
                    
                    if user["quests"][quest_id]["progress"] >= quest["goal"]:
                        user["quests"][quest_id]["completed"] = True
                        # Награда за выполнение квеста
                        UserManager.add_xp(user_id, quest["reward"], "quest")
                        return quest_id, quest["reward"]
        return None, 0

    @staticmethod
    def claim_daily(user_id):
        user = UserManager.get_user_data(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user["last_daily"] == today:
            return False, "Вы уже получали награду сегодня!"
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if user["last_daily"] == yesterday:
            user["daily_streak"] += 1
        else:
            user["daily_streak"] = 1
        
        user["last_daily"] = today
        
        # Базовая награда + бонус за серию
        reward = config["daily_bonus"] + (user["daily_streak"] - 1) * config["streak_bonus"]
        UserManager.add_xp(user_id, reward, "daily")
        
        save_data(data)
        return True, reward

    @staticmethod
    def update_voice_time(user_id, minutes):
        user = UserManager.get_user_data(user_id)
        user["voice_minutes"] += minutes
        user["today_voice"] += minutes * 60
        save_data(data)

    @staticmethod
    def get_warns(user_id):
        user_id = str(user_id)
        return data["warns"].get(user_id, [])

    @staticmethod
    def add_warn(user_id, moderator_id, reason):
        user_id = str(user_id)
        if user_id not in data["warns"]:
            data["warns"][user_id] = []
        
        warn = {
            "moderator": moderator_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "warn_id": len(data["warns"][user_id]) + 1
        }
        data["warns"][user_id].append(warn)
        
        # Обновляем счетчик варнов у пользователя
        user = UserManager.get_user_data(user_id)
        user["warns"] = len(data["warns"][user_id])
        save_data(data)
        
        return warn

    @staticmethod
    def add_achievement(user_id, achievement):
        user = UserManager.get_user_data(user_id)
        if achievement not in user["achievements"]:
            user["achievements"].append(achievement)
            save_data(data)
            return True
        return False

# Система голосового опыта
voice_users = {}

@tasks.loop(seconds=config["voice_xp_interval"])
async def voice_xp_task():
    current_time = datetime.now().timestamp()
    
    for guild in bot.guilds:
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                if member.bot or member.voice.afk or member.voice.self_deaf or member.voice.self_mute:
                    continue
                
                user_id = str(member.id)
                
                if user_id not in voice_users:
                    voice_users[user_id] = {"start_time": current_time, "last_xp": current_time}
                
                # Начисляем XP каждую минуту
                if current_time - voice_users[user_id]["last_xp"] >= 60:
                    minutes_passed = int((current_time - voice_users[user_id]["last_xp"]) / 60)
                    xp_gained = minutes_passed * config["xp_per_minute_voice"]
                    
                    if xp_gained > 0:
                        result = UserManager.add_xp(user_id, xp_gained, "voice")
                        UserManager.update_voice_time(user_id, minutes_passed)
                        voice_users[user_id]["last_xp"] = current_time
                        
                        # Проверяем, повысился ли уровень
                        if result["leveled_up"]:
                            await handle_level_up(member, result["old_level"], result["new_level"])

# Проверка прав модератора
def is_moderator():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        
        for role_name in config["admin_roles"]:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role and role in ctx.author.roles:
                return True
        
        if ctx.author.guild_permissions.manage_messages:
            return True
            
        return False
    return commands.check(predicate)

async def handle_level_up(member, old_level, new_level):
    # Получаем данные пользователя
    user_data = UserManager.get_user_data(member.id)
    fairy = UserManager.get_fairy_type(member.id)
    winx_level = UserManager.get_winx_level(new_level)
    
    # Создаем красивый эмбед
    embed = discord.Embed(
        title="🎉 УРОВЕНЬ ПОВЫШЕН! 🎉",
        description=f"**{member.mention}** достиг нового уровня!",
        color=fairy.value["color"]
    )
    
    # Добавляем иконку феи
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    # Информация об уровнях
    embed.add_field(
        name="📊 Уровни",
        value=f"**Был:** {old_level} уровень\n**Стал:** {new_level} уровень\n**Тип:** {winx_level['name']}",
        inline=True
    )
    
    # Информация о фее
    embed.add_field(
        name=fairy.value["emoji"] + " Сила феи",
        value=f"**Тип:** {fairy.value['name']}\n**Опыт:** {user_data['xp']}",
        inline=True
    )
    
    # Достижения при переходе на важные уровни
    achievements = []
    if new_level >= 5:
        achievements.append("🌟 Фея Чармикс")
        UserManager.add_achievement(member.id, "charmix_fairy")
    if new_level >= 10:
        achievements.append("💫 Фея Энчантикс")
        UserManager.add_achievement(member.id, "enchantix_fairy")
    if new_level >= 20:
        achievements.append("🌸 Фея Созикс")
        UserManager.add_achievement(member.id, "sorceress_fairy")
    
    if achievements:
        embed.add_field(
            name="🏆 Новые достижения",
            value="\n".join(achievements),
            inline=False
        )
    
    # Следующий уровень
    next_level_xp = new_level * config["level_multiplier"]
    progress = (user_data["xp"] / next_level_xp) * 100
    progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
    
    embed.add_field(
        name="📈 Следующий уровень",
        value=f"`{progress_bar}` {progress:.1f}%\nНужно опыта: **{next_level_xp - user_data['xp']}**",
        inline=False
    )
    
    # Отправляем сообщение
    if config["log_channel"]:
        channel = bot.get_channel(config["log_channel"])
        if channel:
            await channel.send(embed=embed)
    else:
        # Пытаемся отправить в общий чат
        for channel in member.guild.text_channels:
            if channel.permissions_for(member.guild.me).send_messages:
                await channel.send(embed=embed)
                break

# События бота
@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    print(f'ID бота: {bot.user.id}')
    
    # Запускаем задачу для голосового опыта
    voice_xp_task.start()
    
    # Запускаем задачу для сброса дневных счетчиков
    reset_daily_counters.start()
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="за магией Винкс"
        )
    )

@bot.event
async def on_guild_join(guild):
    print(f'Бот добавлен на сервер: {guild.name}')
    
    # Создаем роль для мута
    mute_role = discord.utils.get(guild.roles, name=config["mute_role"])
    if not mute_role:
        try:
            mute_role = await guild.create_role(
                name=config["mute_role"],
                color=discord.Color.dark_gray(),
                reason="Роль для мутов"
            )
            
            for channel in guild.channels:
                await channel.set_permissions(
                    mute_role,
                    send_messages=False,
                    add_reactions=False,
                    speak=False
                )
        except Exception as e:
            print(f"Ошибка создания роли мута: {e}")
    
    # Отправляем приветственное сообщение
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="✨ Добро пожаловать в мир магии Винкс! ✨",
                description="Я - бот-фея, который поможет управлять сервером и следить за магическим развитием каждого участника!",
                color=discord.Color.purple()
            )
            
            embed.add_field(
                name="🎮 Основные команды",
                value="• `!rank` - ваш магический профиль\n"
                      "• `!daily` - ежедневная награда\n"
                      "• `!quests` - активные квесты\n"
                      "• `!fairy` - выбрать силу феи",
                inline=False
            )
            
            embed.add_field(
                name="🛡️ Модерация",
                value="• `!clear` - очистить сообщения\n"
                      "• `!mute` - замутить участника\n"
                      "• `!warn` - выдать предупреждение",
                inline=False
            )
            
            embed.add_field(
                name="💫 Получайте опыт",
                value="• Общайтесь в чате\n"
                      "• Проводите время в голосовых каналах\n"
                      "• Выполняйте ежедневные квесты\n"
                      "• Получайте ежедневные награды",
                inline=False
            )
            
            embed.set_footer(text="Развивайте свою магию и становитесь сильнее!")
            
            await channel.send(embed=embed)
            break

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return
    
    user_id = str(message.author.id)
    user_data = UserManager.get_user_data(user_id)
    
    # Проверка кд на получение опыта за сообщения
    current_time = datetime.now().timestamp()
    if current_time - user_data["last_message"] > config["xp_cooldown"]:
        # Начисляем опыт за сообщение
        xp_gained = random.randint(1, config["xp_per_message"])
        
        # Бонус за длинные сообщения
        if len(message.content) > 100:
            xp_gained += int(len(message.content) / 50)
        
        result = UserManager.add_xp(user_id, xp_gained, "message")
        user_data["last_message"] = current_time
        
        # Проверяем, повысился ли уровень
        if result["leveled_up"]:
            await handle_level_up(message.author, result["old_level"], result["new_level"])
        
        save_data(data)
    
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    user_id = str(member.id)
    current_time = datetime.now().timestamp()
    
    # Участник зашел в войс
    if before.channel is None and after.channel is not None:
        if not (after.self_deaf or after.self_mute):
            voice_users[user_id] = {"start_time": current_time, "last_xp": current_time}
    
    # Участник вышел из войса или заглушил себя
    elif (before.channel is not None and after.channel is None) or \
         (after.channel is not None and (after.self_deaf or after.self_mute)):
        if user_id in voice_users:
            session_time = current_time - voice_users[user_id]["start_time"]
            if session_time >= 60:  # Минимум 1 минута
                minutes = int(session_time / 60)
                xp_gained = minutes * config["xp_per_minute_voice"]
                
                if xp_gained > 0:
                    result = UserManager.add_xp(user_id, xp_gained, "voice")
                    UserManager.update_voice_time(user_id, minutes)
                    
                    if result["leveled_up"]:
                        await handle_level_up(member, result["old_level"], result["new_level"])
            
            del voice_users[user_id]

# Задача для сброса дневных счетчиков
@tasks.loop(hours=24)
async def reset_daily_counters():
    now = datetime.now()
    if now.hour == 0:  # В полночь
        for user_id in data["users"]:
            data["users"][user_id]["today_messages"] = 0
            data["users"][user_id]["today_voice"] = 0
        
        # Сброс прогресса дневных квестов
        for user_id in data["users"]:
            for quest_id in list(data["users"][user_id]["quests"].keys()):
                if quest_id in ["daily_messages", "voice_explorer"]:
                    data["users"][user_id]["quests"][quest_id]["progress"] = 0
                    data["users"][user_id]["quests"][quest_id]["completed"] = False
        
        save_data(data)
        print("Дневные счетчики сброшены!")

# КОМАНДЫ WINX

@bot.command(name="rank", aliases=["ранг", "профиль", "магия"])
async def rank(ctx, member: discord.Member = None):
    """Показать магический профиль участника"""
    target = member or ctx.author
    user_id = str(target.id)
    user_data = UserManager.get_user_data(user_id)
    fairy = UserManager.get_fairy_type(user_id)
    winx_level = UserManager.get_winx_level(user_data["level"])
    warns_list = UserManager.get_warns(user_id)
    
    # Вычисляем прогресс
    current_level = user_data["level"]
    xp_needed = current_level * config["level_multiplier"]
    xp_current = user_data["xp"]
    progress = (xp_current / xp_needed) * 100
    
    # Создаем красивый эмбед в стиле Winx
    embed = discord.Embed(
        title=f"{fairy.value['emoji']} Магический профиль {target.display_name}",
        color=fairy.value["color"]
    )
    
    # Аватарка пользователя
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    
    # Основная информация
    embed.add_field(
        name="✨ Уровень феи",
        value=f"**{current_level} уровень**\n{winx_level['name']}",
        inline=True
    )
    
    embed.add_field(
        name=f"{fairy.value['emoji']} Сила феи",
        value=fairy.value["name"],
        inline=True
    )
    
    embed.add_field(
        name="📊 Опыт",
        value=f"**{user_data['total_xp']}** всего\n**{xp_current}/{xp_needed}** до след. ур.",
        inline=True
    )
    
    # Прогресс-бар
    progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
    embed.add_field(
        name="📈 Прогресс",
        value=f"`{progress_bar}` **{progress:.1f}%**",
        inline=False
    )
    
    # Статистика
    embed.add_field(
        name="📝 Активность",
        value=f"**Сообщений:** {user_data['messages']}\n"
              f"**В голосовых:** {user_data['voice_minutes']} мин.\n"
              f"**Сегодня:** {user_data['today_messages']} сообщ.",
        inline=True
    )
    
    embed.add_field(
        name="🏆 Достижения",
        value=f"**Достижений:** {len(user_data['achievements'])}\n"
              f"**Серия дней:** {user_data['daily_streak']}\n"
              f"**Предупреждений:** {len(warns_list)}",
        inline=True
    )
    
    # Следующий уровень Winx
    next_winx = None
    for lvl in sorted(WINX_LEVELS.keys()):
        if lvl > current_level:
            next_winx = WINX_LEVELS[lvl]
            break
    
    if next_winx:
        embed.add_field(
            name="🎯 До следующего титула",
            value=f"**{next_winx['name']}**\n"
                  f"Нужно: {next_winx['xp_required'] - user_data['total_xp']} опыта",
            inline=False
        )
    
    # Достижения (первые 3)
    if user_data["achievements"]:
        achievements_display = "\n".join(f"• {ach}" for ach in user_data["achievements"][:3])
        if len(user_data["achievements"]) > 3:
            achievements_display += f"\n...и ещё {len(user_data['achievements']) - 3}"
        embed.add_field(name="🏅 Последние достижения", value=achievements_display, inline=False)
    
    embed.set_footer(text="Развивай свою магию каждый день!")
    
    await ctx.send(embed=embed)

@bot.command(name="fairy", aliases=["фея", "сила"])
async def fairy_cmd(ctx, fairy_name: str = None):
    """Выбрать или посмотреть свою силу феи"""
    if fairy_name:
        if UserManager.set_fairy_type(ctx.author.id, fairy_name):
            fairy = UserManager.get_fairy_type(ctx.author.id)
            
            embed = discord.Embed(
                title="✨ Сила феи изменена! ✨",
                description=f"Теперь твоя магия - **{fairy.value['name']}**",
                color=fairy.value["color"]
            )
            
            # Описание сил феи
            fairy_descriptions = {
                "BLOOM": "🔥 Огненная магия дракона. Сила страсти и защиты.",
                "STELLA": "✨ Магия солнца и луны. Сила света и красоты.",
                "FLORA": "🌿 Магия природы и растений. Сила роста и исцеления.",
                "MUSHA": "💧 Магия музыки и волн. Сила гармонии и эмоций.",
                "TECNA": "⚡ Магия технологий и логики. Сила разума и порядка.",
                "LAYLA": "💎 Магия воды и форм. Сила адаптации и моря."
            }
            
            embed.add_field(
                name="📖 Описание силы",
                value=fairy_descriptions.get(fairy.name, "Тайная древняя магия."),
                inline=False
            )
            
            # Бонусы
            embed.add_field(
                name="💫 Особенности",
                value="• Уникальные реакции\n• Специальные фразы\n• Магические аватары",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Доступные силы феи:\n"
                          "• **bloom** - 🔥 Огненная магия\n"
                          "• **stella** - ✨ Световая магия\n"
                          "• **flora** - 🌿 Природная магия\n"
                          "• **musha** - 💧 Музыкальная магия\n"
                          "• **tecna** - ⚡ Техно-магия\n"
                          "• **layla** - 💎 Водная магия",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    else:
        fairy = UserManager.get_fairy_type(ctx.author.id)
        
        embed = discord.Embed(
            title=f"{fairy.value['emoji']} Твоя сила феи",
            description=f"**{fairy.value['name']}**",
            color=fairy.value["color"]
        )
        
        await ctx.send(embed=embed)

@bot.command(name="daily", aliases=["ежедневно", "награда"])
async def daily(ctx):
    """Получить ежедневную награду"""
    success, message = UserManager.claim_daily(ctx.author.id)
    
    if success:
        fairy = UserManager.get_fairy_type(ctx.author.id)
        user_data = UserManager.get_user_data(ctx.author.id)
        
        embed = discord.Embed(
            title="🎁 Ежедневная награда получена!",
            description=f"Ты получил **{message}** магических очков!",
            color=fairy.value["color"]
        )
        
        embed.add_field(
            name="💫 Серия дней",
            value=f"Текущая серия: **{user_data['daily_streak']} дней**",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Завтра получишь",
            value=f"**{config['daily_bonus'] + (user_data['daily_streak']) * config['streak_bonus']}** очков",
            inline=True
        )
        
        # Прогресс до следующего уровня
        next_level_xp = user_data["level"] * config["level_multiplier"]
        progress = (user_data["xp"] / next_level_xp) * 100
        progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        
        embed.add_field(
            name="📈 Прогресс уровня",
            value=f"`{progress_bar}` {progress:.1f}%",
            inline=False
        )
        
        embed.set_footer(text="Возвращайся завтра за новой наградой!")
        
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="⏳ Уже получал сегодня",
            description=message,
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

@bot.command(name="quests", aliases=["квесты", "задания"])
async def quests(ctx):
    """Показать активные квесты"""
    user_data = UserManager.get_user_data(ctx.author.id)
    fairy = UserManager.get_fairy_type(ctx.author.id)
    
    embed = discord.Embed(
        title="📋 Магические квесты",
        description="Выполняй задания для получения опыта!",
        color=fairy.value["color"]
    )
    
    for quest_id, quest in QUESTS.items():
        if quest_id in user_data.get("quests", {}):
            quest_data = user_data["quests"][quest_id]
            status = "✅ Выполнен" if quest_data["completed"] else f"📊 {quest_data['progress']}/{quest['goal']}"
        else:
            status = "🆕 Не начат"
        
        embed.add_field(
            name=f"{quest['name']} | {quest['reward']} опыта",
            value=f"{quest['description']}\n**Статус:** {status}",
            inline=False
        )
    
    if not QUESTS:
        embed.description = "На данный момент квестов нет."
    
    embed.set_footer(text="Квесты обновляются ежедневно!")
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["топ", "лидеры", "маги"])
async def leaderboard(ctx, category: str = "xp"):
    """Топ участников по разным категориям"""
    categories = {
        "xp": {"name": "🔮 По опыту", "key": "total_xp"},
        "level": {"name": "🌟 По уровню", "key": "level"},
        "messages": {"name": "💬 По сообщениям", "key": "messages"},
        "voice": {"name": "🎤 По голосовой активности", "key": "voice_minutes"},
        "streak": {"name": "🔥 По серии дней", "key": "daily_streak"}
    }
    
    cat = categories.get(category.lower(), categories["xp"])
    
    # Собираем данные
    members_data = []
    for member in ctx.guild.members:
        if not member.bot:
            user_id = str(member.id)
            if user_id in data["users"]:
                user_data = data["users"][user_id]
                members_data.append({
                    "member": member,
                    "value": user_data[cat["key"]],
                    "level": user_data["level"],
                    "xp": user_data["total_xp"]
                })
    
    # Сортируем
    members_data.sort(key=lambda x: x["value"], reverse=True)
    
    fairy = UserManager.get_fairy_type(ctx.author.id)
    embed = discord.Embed(
        title=f"🏆 {cat['name']}",
        color=fairy.value["color"]
    )
    
    for i, member_data in enumerate(members_data[:10], 1):
        medal = ""
        if i == 1: medal = "🥇 "
        elif i == 2: medal = "🥈 "
        elif i == 3: medal = "🥉 "
        
        value_display = member_data["value"]
        if category == "voice":
            value_display = f"{value_display} мин."
        
        embed.add_field(
            name=f"{medal}{i}. {member_data['member'].display_name}",
            value=f"**{cat['name'].split(' ')[1]}:** {value_display}\n"
                  f"Уровень: {member_data['level']} | Опыт: {member_data['xp']}",
            inline=False
        )
    
    if not members_data:
        embed.description = "Пока нет данных об участниках."
    
    embed.set_footer(text=f"Используй !leaderboard [xp/level/messages/voice/streak]")
    await ctx.send(embed=embed)

@bot.command(name="magic", aliases=["магияинфо"])
async def magic_info(ctx):
    """Информация о магической системе"""
    fairy = UserManager.get_fairy_type(ctx.author.id)
    
    embed = discord.Embed(
        title="✨ Система магии Винкс ✨",
        description="Как развивать свою магическую силу:",
        color=fairy.value["color"]
    )
    
    embed.add_field(
        name="📝 Опыт за сообщения",
        value=f"• **1-{config['xp_per_message']} XP** за сообщение\n• КД: {config['xp_cooldown']} секунд\n• Бонус за длинные сообщения",
        inline=False
    )
    
    embed.add_field(
        name="🎤 Опыт в голосовых",
        value=f"• **{config['xp_per_minute_voice']} XP** в минуту\n• Только в активных каналах\n• AFK/заглушенные не получают XP",
        inline=False
    )
    
    embed.add_field(
        name="🎁 Ежедневные награды",
        value=f"• Базовая: **{config['daily_bonus']} XP**\n• Бонус за серию: **+{config['streak_bonus']} XP**/день\n• Макс. серия: неограничена",
        inline=False
    )
    
    embed.add_field(
        name="🌟 Уровни феи",
        value="• **1-4:** Обычная фея\n• **5-9:** Фея Чармикс\n• **10-14:** Фея Энчантикс\n• **15-19:** Фея Белэвикс\n• **20+:** Легендарные формы",
        inline=False
    )
    
    embed.add_field(
        name="💫 Типы фей",
        value="• 🔥 **Блум** - огонь\n• ✨ **Стелла** - свет\n• 🌿 **Флора** - природа\n• 💧 **Муза** - музыка\n• ⚡ **Текна** - технологии\n• 💎 **Лейла** - вода",
        inline=False
    )
    
    embed.set_footer(text="Используй !fairy [имя] чтобы выбрать свою силу!")
    await ctx.send(embed=embed)

@bot.command(name="achievements", aliases=["достижения"])
async def achievements_cmd(ctx, member: discord.Member = None):
    """Показать достижения участника"""
    target = member or ctx.author
    user_data = UserManager.get_user_data(target.id)
    fairy = UserManager.get_fairy_type(target.id)
    
    if not user_data["achievements"]:
        embed = discord.Embed(
            title="🏅 Достижения",
            description=f"У {target.mention} пока нет достижений.\nПродолжай развивать свою магию!",
            color=fairy.value["color"]
        )
    else:
        embed = discord.Embed(
            title=f"🏅 Достижения {target.display_name}",
            description=f"Всего достижений: **{len(user_data['achievements'])}**",
            color=fairy.value["color"]
        )
        
        # Группируем достижения
        for i, achievement in enumerate(user_data["achievements"][:15], 1):
            embed.add_field(
                name=f"{i}. {achievement}",
                value="────────",
                inline=True
            )
        
        if len(user_data["achievements"]) > 15:
            embed.set_footer(text=f"Показано 15 из {len(user_data['achievements'])} достижений")
    
    await ctx.send(embed=embed)

# Команды модерации (обновленные в стиле Winx)

@bot.command(name="magicmute", aliases=["магическиймут"])
@is_moderator()
async def magic_mute(ctx, member: discord.Member, time: int = 60, *, reason="Магическое нарушение"):
    """Замутить участника магическим заклинанием"""
    mute_role = discord.utils.get(ctx.guild.roles, name=config["mute_role"])
    if not mute_role:
        await ctx.send("❌ Магическая печать не найдена!")
        return
    
    fairy = UserManager.get_fairy_type(ctx.author.id)
    
    await member.add_roles(mute_role, reason=reason)
    
    embed = discord.Embed(
        title="🔇 Магический мут наложен!",
        description="Сила фей временно заблокирована.",
        color=fairy.value["color"]
    )
    embed.add_field(name="🎭 Фея", value=member.mention, inline=True)
    embed.add_field(name="✨ Модератор-фея", value=ctx.author.mention, inline=True)
    embed.add_field(name="⏳ Время", value=f"{time} минут", inline=True)
    embed.add_field(name="📖 Причина", value=reason, inline=False)
    
    await ctx.send(embed=embed)
    
    if time > 0:
        await asyncio.sleep(time * 60)
        if mute_role in member.roles:
            await member.remove_roles(mute_role, reason="Магия восстановлена")
            
            embed = discord.Embed(
                description=f"🔊 {member.mention}, твоя магия восстановлена!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

@bot.command(name="magicwarn", aliases=["магическоепред"])
@is_moderator()
async def magic_warn(ctx, member: discord.Member, *, reason="Магическое предупреждение"):
    """Выдать магическое предупреждение"""
    warn = UserManager.add_warn(member.id, ctx.author.id, reason)
    warns_count = len(UserManager.get_warns(member.id))
    
    fairy = UserManager.get_fairy_type(ctx.author.id)
    
    embed = discord.Embed(
        title="⚠️ Магическое предупреждение!",
        description="Твоя магия под наблюдением.",
        color=fairy.value["color"]
    )
    embed.add_field(name="🎭 Фея", value=member.mention, inline=True)
    embed.add_field(name="✨ Модератор-фея", value=ctx.author.mention, inline=True)
    embed.add_field(name="📊 Всего предупреждений", value=warns_count, inline=True)
    embed.add_field(name="📖 Причина", value=reason, inline=False)
    embed.set_footer(text=f"ID предупреждения: {warn['warn_id']}")
    
    await ctx.send(embed=embed)
    
    # Магические последствия
    if warns_count >= 3:
        mute_role = discord.utils.get(ctx.guild.roles, name=config["mute_role"])
        if mute_role:
            await member.add_roles(mute_role, reason="3 магических предупреждения")
            
            embed = discord.Embed(
                description=f"🔇 {member.mention} получил мут на 60 минут за 3 предупреждения.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
            await asyncio.sleep(3600)
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Магия восстановлена")

# Команды администратора
@bot.command(name="addxp", aliases=["датьопыт"])
@is_moderator()
async def add_xp_cmd(ctx, member: discord.Member, amount: int):
    """Добавить опыт участнику (только для модераторов)"""
    result = UserManager.add_xp(member.id, amount, "moderator")
    
    fairy = UserManager.get_fairy_type(member.id)
    user_data = UserManager.get_user_data(member.id)
    
    embed = discord.Embed(
        title="✨ Магический опыт добавлен!",
        description=f"{member.mention} получил **{amount}** магических очков!",
        color=fairy.value["color"]
    )
    
    embed.add_field(name="🎯 Текущий опыт", value=f"**{user_data['total_xp']}**", inline=True)
    embed.add_field(name="🌟 Уровень", value=f"**{user_data['level']}**", inline=True)
    
    if result["leveled_up"]:
        embed.add_field(
            name="🎉 Новый уровень!",
            value=f"Был: {result['old_level']} | Стал: {result['new_level']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name="resetfairy", aliases=["сброситьфею"])
@is_moderator()
async def reset_fairy(ctx, member: discord.Member):
    """Сбросить тип феи участника"""
    user_data = UserManager.get_user_data(member.id)
    old_fairy = user_data.get("fairy_type", "Не выбрана")
    
    # Сбрасываем тип феи
    user_data["fairy_type"] = None
    save_data(data)
    
    embed = discord.Embed(
        title="🔄 Тип феи сброшен!",
        description=f"{member.mention} может выбрать новую магическую силу.",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="📖 Старая сила", value=old_fairy, inline=True)
    embed.add_field(name="✨ Новая сила", value="Не выбрана", inline=True)
    
    await ctx.send(embed=embed)

# Команда помощи в стиле Winx
@bot.command(name="help", aliases=["помощь", "магическаяпомощь"])
async def help_command(ctx):
    """Показать магические команды"""
    fairy = UserManager.get_fairy_type(ctx.author.id)
    
    embed = discord.Embed(
        title="📚 Магическая книга команд 📚",
        description="Все заклинания и команды бота-феи",
        color=fairy.value["color"]
    )
    
    embed.add_field(
        name=f"{fairy.value['emoji']} Магия и развитие",
        value="• `!rank` - магический профиль\n"
              "• `!fairy [тип]` - выбрать силу феи\n"
              "• `!daily` - ежедневная награда\n"
              "• `!quests` - активные квесты\n"
              "• `!leaderboard` - топ магов\n"
              "• `!magic` - информация о системе\n"
              "• `!achievements` - твои достижения",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Магическая модерация",
        value="• `!clear [число]` - очистить сообщения\n"
              "• `!magicmute @фея [время] [причина]`\n"
              "• `!magicwarn @фея [причина]`\n"
              "• `!warns @фея` - предупреждения\n"
              "• `!kick` / `!ban` - стандартные команды",
        inline=False
    )
    
    embed.add_field(
        name="✨ Для модераторов-фей",
        value="• `!addxp @фея [число]` - дать опыт\n"
              "• `!resetfairy @фея` - сбросить силу\n"
              "• `!setlog #канал` - канал для логов\n"
              "• `!config` - настройки бота",
        inline=False
    )
    
    embed.set_footer(text=f"Твоя сила: {fairy.value['name']} | Префикс: !")
    
    await ctx.send(embed=embed)

# Запуск бота
if __name__ == "__main__":
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    print("""
    ╔══════════════════════════════════════╗
    ║     ✨ Бот-фея Winx Club запускается!✨   ║
    ║     Магия активируется...            ║
    ╚══════════════════════════════════════╝
    """)
    
    print("Не забудьте заменить 'YOUR_BOT_TOKEN_HERE' на ваш токен!")
    print("\nОсобенности бота:")
    print("• Система уровней в стиле Winx Club")
    print("• 6 типов фей с уникальными цветами")
    print("• Опыт за сообщения и голосовую активность")
    print("• Ежедневные награды и квесты")
    print("• Магические команды модерации")
    print("• Достижения и прогрессия")
    
    bot.run(TOKEN)
  
