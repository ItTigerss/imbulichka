import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Словарь с РП действиями и соответствующими эмодзи/цветами
rp_actions = {
    'обнять': {
        'text': '🤗 **{author}** обнял(а) **{target}**!',
        'color': 0xff69b4,
        'gifs': [
            'https://media.tenor.com/TEST1.gif',
            'https://media.tenor.com/TEST2.gif'
        ]
    },
    'погладить': {
        'text': '😊 **{author}** гладит **{target}** по голове.',
        'color': 0x98fb98,
        'gifs': []
    },
    'укусить': {
        'text': '😲 **{author}** укусил(а) **{target}**!',
        'color': 0xff4500,
        'gifs': []
    }
}

# --- Интерактивное меню с кнопками ---
class HelpMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="🎮 РП команды", style=discord.ButtonStyle.primary, row=0)
    async def rp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Ролевые команды", 
            description="Доступные команды:\n!обнять @пользователь\n!погладить @пользователь\n!укусить @пользователь",
            color=0x9b59b6
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❓ Помощь", style=discord.ButtonStyle.secondary, row=0)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Помощь по боту",
            description="Используйте !меню для вызова этого меню\n!команды для списка всех команд",
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Меню закрыто.", view=None)

@bot.command(name='меню')
async def show_menu(ctx):
    """Показывает интерактивное меню помощи."""
    embed = discord.Embed(
        title="🌟 Интерактивное меню", 
        description="Нажмите на кнопки ниже для получения информации:", 
        color=0x9b59b6
    )
    await ctx.send(embed=embed, view=HelpMenu())

@bot.command(name='команды')
async def list_commands(ctx):
    """Показывает список всех команд."""
    embed = discord.Embed(title="📋 Список команд", color=0x3498db)
    embed.add_field(name="Основные", value="!меню - показать интерактивное меню\n!команды - этот список", inline=False)
    embed.add_field(name="РП команды", value="!обнять @user\n!погладить @user\n!укусить @user", inline=False)
    await ctx.send(embed=embed)

# --- РП команды ---
@bot.command(name='обнять')
async def hug(ctx, member: discord.Member = None):
    """Обнять пользователя."""
    if member is None:
        await ctx.send("❌ Укажите пользователя! Например: `!обнять @username`")
        return
    await send_rp_action(ctx, 'обнять', member)

@bot.command(name='погладить')
async def pat(ctx, member: discord.Member = None):
    """Погладить пользователя."""
    if member is None:
        await ctx.send("❌ Укажите пользователя! Например: `!погладить @username`")
        return
    await send_rp_action(ctx, 'погладить', member)

@bot.command(name='укусить')
async def bite(ctx, member: discord.Member = None):
    """Укусить пользователя."""
    if member is None:
        await ctx.send("❌ Укажите пользователя! Например: `!укусить @username`")
        return
    await send_rp_action(ctx, 'укусить', member)

async def send_rp_action(ctx, action_key, target):
    """Вспомогательная функция для отправки РП действий."""
    if target == ctx.author:
        await ctx.send("❌ Нельзя применить это действие к самому себе!")
        return
    
    action_data = rp_actions.get(action_key)
    if not action_data:
        await ctx.send("❌ Действие не найдено!")
        return
    
    message = action_data['text'].format(author=ctx.author.mention, target=target.mention)
    
    embed = discord.Embed(description=message, color=action_data['color'])
    
    # Добавляем случайную гифку, если они есть
    if action_data['gifs'] and random.choice([True, False]):
        embed.set_image(url=random.choice(action_data['gifs']))
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Обработчик ошибок команд."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Пропущен обязательный аргумент. Используйте `!команды` для справки.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный аргумент. Проверьте правильность ввода.")
    else:
        await ctx.send(f"❌ Произошла ошибка: {str(error)}")

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} успешно подключен!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    print(f'🎮 Команды загружены: {len(bot.commands)}')

# Запуск бота
if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем токен из переменных окружения
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ОШИБКА: Токен не найден!")
        print("🔑 Создайте файл .env в папке проекта и добавьте:")
        print("DISCORD_TOKEN=ваш_токен_бота")
        print("📝 Получите токен: https://discord.com/developers/applications")
        print("\n💡 После создания .env файла, запустите бота снова.")
    else:
        print("✅ Токен загружен из .env файла")
        print(f"🔑 Токен (первые 5 символов): {TOKEN[:5]}...")
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Ошибка: Неверный токен бота!")
            print("💡 Возможно, токен был скомпрометирован. Сбросьте его в Discord Developer Portal.")
        except Exception as e:
            print(f"❌ Ошибка при запуске: {e}")