import discord
from discord.ext import commands
import random
import os
import json
import datetime
import asyncio
from dotenv import load_dotenv
from collections import defaultdict
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Bot settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Отключаем встроенную команду help

# File for level data
LEVELS_FILE = 'levels.json'

# Load level data
def load_levels():
    if os.path.exists(LEVELS_FILE):
        with open(LEVELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save level data
def save_levels(data):
    with open(LEVELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# User level data
user_levels = load_levels()

# Anti-spam tracking
last_message_time = defaultdict(dict)

# --- RP COMMANDS BY CATEGORY (24 commands total) ---

rp_categories = {
    "affection": {
        "name": "💕 Affection",
        "color": 0xff69b4,
        "description": "Warm and loving actions",
        "commands": {
            'hug': {
                'text': '🤗 **{author}** hugged **{target}**!',
                'gifs': [
                    'https://media.tenor.com/2qF4uSeT-gcAAAAC/anime-hug.gif',
                    'https://media.tenor.com/2WUN1q7uU0EAAAAC/hug-anime.gif'
                ]
            },
            'kiss': {
                'text': '😘 **{author}** kissed **{target}**!',
                'gifs': [
                    'https://media.tenor.com/G4M6qVw7U8EAAAAC/anime-kiss.gif',
                    'https://media.tenor.com/gG1yBqWqWqkAAAAC/kiss-anime.gif'
                ]
            },
            'cuddle': {
                'text': '🥰 **{author}** cuddled with **{target}**!',
                'gifs': [
                    'https://media.tenor.com/2xV1mRQZ0n4AAAAC/anime-cuddle.gif'
                ]
            },
            'pat': {
                'text': '😊 **{author}** patted **{target}** on the head!',
                'gifs': [
                    'https://media.tenor.com/BJ2y7q0tGQYAAAAC/anime-pat.gif',
                    'https://media.tenor.com/7RX-pPpNxBkAAAAC/pat-head-pat.gif'
                ]
            },
            'boop': {
                'text': '👆 **{author}** booped **{target}**!',
                'gifs': []
            }
        }
    },
    "playful": {
        "name": "🎉 Playful",
        "color": 0xffa500,
        "description": "Fun and silly interactions",
        "commands": {
            'poke': {
                'text': '👉 **{author}** poked **{target}**!',
                'gifs': []
            },
            'tickle': {
                'text': '😂 **{author}** tickled **{target}**!',
                'gifs': []
            },
            'dance': {
                'text': '💃 **{author}** danced with **{target}**!',
                'gifs': []
            },
            'highfive': {
                'text': '🖐️ **{author}** gave a high-five to **{target}**!',
                'gifs': []
            },
            'wave': {
                'text': '👋 **{author}** waved at **{target}**!',
                'gifs': []
            },
            'cheer': {
                'text': '🎉 **{author}** cheered for **{target}**!',
                'gifs': []
            }
        }
    },
    "mischief": {
        "name": "😈 Mischief",
        "color": 0xff4500,
        "description": "Playful teasing and trouble",
        "commands": {
            'bite': {
                'text': '😲 **{author}** bit **{target}**!',
                'gifs': [
                    'https://media.tenor.com/bKQY_b9x2lIAAAAC/anime-bite.gif'
                ]
            },
            'slap': {
                'text': '👋 **{author}** slapped **{target}**!',
                'gifs': [
                    'https://media.tenor.com/0O9qTZ8qWqkAAAAC/anime-slap.gif'
                ]
            },
            'pinch': {
                'text': '🤏 **{author}** pinched **{target}**!',
                'gifs': []
            },
            'push': {
                'text': '👋 **{author}** pushed **{target}**!',
                'gifs': []
            },
            'throw': {
                'text': '🤾 **{author}** threw **{target}**!',
                'gifs': []
            }
        }
    },
    "caring": {
        "name": "💝 Caring",
        "color": 0x98fb98,
        "description": "Sweet and supportive actions",
        "commands": {
            'cookie': {
                'text': '🍪 **{author}** gave a cookie to **{target}**!',
                'gifs': []
            },
            'cake': {
                'text': '🎂 **{author}** gave cake to **{target}**!',
                'gifs': []
            },
            'coffee': {
                'text': '☕ **{author}** gave coffee to **{target}**!',
                'gifs': []
            },
            'protect': {
                'text': '🛡️ **{author}** protected **{target}**!',
                'gifs': []
            },
            'comfort': {
                'text': '🤗 **{author}** comforted **{target}**!',
                'gifs': []
            }
        }
    },
    "reactions": {
        "name": "😊 Reactions",
        "color": 0x9b59b6,
        "description": "Express your feelings",
        "commands": {
            'smile': {
                'text': '😊 **{author}** smiled at **{target}**!',
                'gifs': []
            },
            'blush': {
                'text': '😳 **{author}** blushed at **{target}**!',
                'gifs': []
            },
            'cry': {
                'text': '😢 **{author}** cried on **{target}**!',
                'gifs': []
            },
            'laugh': {
                'text': '😂 **{author}** laughed at **{target}**!',
                'gifs': []
            },
            'angry': {
                'text': '😠 **{author}** is angry at **{target}**!',
                'gifs': []
            }
        }
    }
}

# Flatten for easy access
rp_actions = {}
for category, data in rp_categories.items():
    for cmd_name, cmd_data in data["commands"].items():
        rp_actions[cmd_name] = {
            "text": cmd_data["text"],
            "color": data["color"],
            "gifs": cmd_data["gifs"],
            "category": category,
            "category_name": data["name"]
        }

# --- PAGINATED MENUS ---

class PaginatedView(discord.ui.View):
    """Base class for paginated views"""
    def __init__(self, embeds, timeout=180):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update the state of navigation buttons"""
        self.first_page.disabled = self.current_page == 0
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == self.total_pages - 1
        self.last_page.disabled = self.current_page == self.total_pages - 1
        
        # Update page counter
        self.page_counter.label = f"📄 {self.current_page + 1}/{self.total_pages}"
    
    @discord.ui.button(label="⏪ First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="📄 1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Just a page counter, no action"""
        pass
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="⏩ Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

class CategoryRPView(discord.ui.View):
    """View for selecting RP command categories"""
    def __init__(self):
        super().__init__(timeout=180)
    
    @discord.ui.button(label="💕 Affection", style=discord.ButtonStyle.primary, emoji="💕", row=0)
    async def affection_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_category_pages("affection")
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("categories"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="🎉 Playful", style=discord.ButtonStyle.success, emoji="🎉", row=0)
    async def playful_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_category_pages("playful")
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("categories"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="😈 Mischief", style=discord.ButtonStyle.danger, emoji="😈", row=1)
    async def mischief_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_category_pages("mischief")
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("categories"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="💝 Caring", style=discord.ButtonStyle.success, emoji="💝", row=1)
    async def caring_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_category_pages("caring")
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("categories"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="😊 Reactions", style=discord.ButtonStyle.secondary, emoji="😊", row=2)
    async def reactions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_category_pages("reactions")
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("categories"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="◀️ Back to Main", style=discord.ButtonStyle.secondary, row=3)
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🌟 Main Menu", 
            description="Select a category:", 
            color=0x9b59b6
        )
        await interaction.response.edit_message(embed=embed, view=MainMenu())
    
    @discord.ui.button(label="✖️ Close", style=discord.ButtonStyle.danger, row=3)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Menu closed.", embed=None, view=None)
    
    def create_back_button(self, target):
        button = discord.ui.Button(label="◀️ Back to Categories", style=discord.ButtonStyle.secondary)
        
        async def back_callback(interaction: discord.Interaction):
            embed = create_categories_embed()
            await interaction.response.edit_message(embed=embed, view=CategoryRPView())
        
        button.callback = back_callback
        return button
    
    def create_close_button(self):
        button = discord.ui.Button(label="✖️ Close", style=discord.ButtonStyle.danger)
        
        async def close_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Menu closed.", embed=None, view=None)
        
        button.callback = close_callback
        return button

class MainMenu(discord.ui.View):
    """Main menu with category buttons"""
    def __init__(self):
        super().__init__(timeout=180)
    
    @discord.ui.button(label="🎭 RP Commands", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def rp_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_categories_embed()
        await interaction.response.edit_message(embed=embed, view=CategoryRPView())
    
    @discord.ui.button(label="⭐ Level System", style=discord.ButtonStyle.success, emoji="📊", row=0)
    async def level_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_level_pages()
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("main"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="🔧 Utilities", style=discord.ButtonStyle.secondary, emoji="🛠️", row=0)
    async def utils_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = create_utils_pages()
        view = PaginatedView(embeds)
        view.add_item(self.create_back_button("main"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    @discord.ui.button(label="ℹ️ About", style=discord.ButtonStyle.secondary, emoji="🤖", row=1)
    async def about_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_about_embed()
        view = discord.ui.View(timeout=180)
        view.add_item(self.create_back_button("main"))
        view.add_item(self.create_close_button())
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="✖️ Close", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Menu closed.", embed=None, view=None)
    
    def create_back_button(self, target):
        button = discord.ui.Button(label="◀️ Back to Main", style=discord.ButtonStyle.secondary)
        
        async def back_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🌟 Main Menu", 
                description="Select a category:", 
                color=0x9b59b6
            )
            await interaction.response.edit_message(embed=embed, view=MainMenu())
        
        button.callback = back_callback
        return button
    
    def create_close_button(self):
        button = discord.ui.Button(label="✖️ Close", style=discord.ButtonStyle.danger)
        
        async def close_callback(interaction: discord.Interaction):
            await interaction.response.edit_message(content="Menu closed.", embed=None, view=None)
        
        button.callback = close_callback
        return button

# --- PAGE CREATION FUNCTIONS ---

def create_categories_embed():
    """Create embed showing all RP categories"""
    embed = discord.Embed(
        title="🎭 RP Command Categories",
        description="Select a category to see available commands:",
        color=0xff69b4
    )
    
    for cat_id, cat_data in rp_categories.items():
        embed.add_field(
            name=f"{cat_data['name']}",
            value=f"{cat_data['description']}\n*{len(cat_data['commands'])} commands*",
            inline=True
        )
    
    embed.set_footer(text=f"Total RP Commands: {len(rp_actions)} • Click a category below")
    return embed

def create_category_pages(category_id: str) -> List[discord.Embed]:
    """Create paginated pages for a specific category"""
    category = rp_categories[category_id]
    pages = []
    commands_per_page = 4
    
    commands_list = list(category["commands"].items())
    total_pages = (len(commands_list) + commands_per_page - 1) // commands_per_page
    
    for page_num in range(total_pages):
        start_idx = page_num * commands_per_page
        end_idx = min(start_idx + commands_per_page, len(commands_list))
        
        embed = discord.Embed(
            title=f"{category['name']} Commands (Page {page_num + 1}/{total_pages})",
            description=category["description"],
            color=category["color"]
        )
        
        for cmd_name, cmd_data in commands_list[start_idx:end_idx]:
            example = cmd_data["text"].format(author="You", target="@user")
            embed.add_field(
                name=f"!{cmd_name} @user",
                value=example,
                inline=False
            )
        
        embed.set_footer(text=f"Category: {category['name']} • Use buttons to navigate")
        pages.append(embed)
    
    return pages

def create_level_pages():
    """Create paginated level system pages"""
    pages = []
    
    # Page 1: How it works
    embed1 = discord.Embed(
        title="⭐ Level System (1/3) - How It Works",
        description="**Earning Experience:**\n"
                   "• **Messages:** 10-20 XP per message (30s cooldown)\n"
                   "• **Voice Chat:** 5 XP per minute (not alone)\n"
                   "• **RP Commands:** 5 XP per use\n\n"
                   "**Level Formula:**\n"
                   "• XP needed = 100 × (level²)\n"
                   "• Level 1 → 100 XP\n"
                   "• Level 2 → 400 XP\n"
                   "• Level 3 → 900 XP",
        color=0xffd700
    )
    embed1.set_footer(text="Page 1/3 • Use buttons to navigate")
    pages.append(embed1)
    
    # Page 2: Commands
    embed2 = discord.Embed(
        title="⭐ Level System (2/3) - Commands",
        description="**Available Commands:**\n\n"
                   "`!profile [@user]` - View user profile\n"
                   "`!level` - Your current level\n"
                   "`!top` - Leaderboard\n"
                   "`!rank [@user]` - User ranking",
        color=0xffd700
    )
    embed2.set_footer(text="Page 2/3 • Use buttons to navigate")
    pages.append(embed2)
    
    # Page 3: Rewards
    embed3 = discord.Embed(
        title="⭐ Level System (3/3) - Rewards",
        description="**Level Rewards:**\n\n"
                   "• **Level 5:** 🎮 Access to games\n"
                   "• **Level 10:** 🎨 Custom color role\n"
                   "• **Level 20:** 🎤 Priority voice\n"
                   "• **Level 30:** 👑 Special commands\n"
                   "• **Level 50:** 💎 Elite role",
        color=0xffd700
    )
    embed3.set_footer(text="Page 3/3 • Use buttons to navigate")
    pages.append(embed3)
    
    return pages

def create_utils_pages():
    """Create paginated utilities pages"""
    pages = []
    
    # Page 1: Basic commands
    embed1 = discord.Embed(
        title="🔧 Utilities (1/2) - Basic Commands",
        description="**Command List:**\n\n"
                   "`!ping` - Check bot latency\n"
                   "`!server` - Server information\n"
                   "`!user [@user]` - User information\n"
                   "`!avatar [@user]` - Show user avatar\n"
                   "`!random [min] [max]` - Random number",
        color=0x3498db
    )
    embed1.set_footer(text="Page 1/2 • Use buttons to navigate")
    pages.append(embed1)
    
    # Page 2: Fun commands
    embed2 = discord.Embed(
        title="🔧 Utilities (2/2) - Fun Commands",
        description="**Fun Commands:**\n\n"
                   "`!coinflip` - Flip a coin\n"
                   "`!dice` - Roll a dice\n"
                   "`!choose opt1, opt2, ...` - Choose option\n"
                   "`!8ball question` - Magic 8-ball",
        color=0x3498db
    )
    embed2.set_footer(text="Page 2/2 • Use buttons to navigate")
    pages.append(embed2)
    
    return pages

def create_about_embed():
    """Create about embed"""
    embed = discord.Embed(
        title="🤖 About This Bot",
        description="A multifunctional Discord bot with leveling system, RP commands, and interactive menus.",
        color=0x9b59b6
    )
    embed.add_field(name="Version", value="3.0.0", inline=True)
    embed.add_field(name="Creator", value="iimbulchka", inline=True)
    embed.add_field(name="Commands", value=f"{len(bot.commands) + len(rp_actions)}+", inline=True)
    embed.add_field(name="RP Commands", value=f"**{len(rp_actions)}** in 5 categories", inline=True)
    embed.add_field(name="Features", value="• Level System\n• RP Commands by Category\n• Paginated Menus\n• Voice XP\n• Utilities", inline=False)
    embed.set_footer(text="Thanks for using this bot!")
    return embed

# --- COMMANDS ---

@bot.command(name='menu')
async def show_menu(ctx):
    """Show the main interactive menu"""
    embed = discord.Embed(
        title="🌟 Main Menu", 
        description="Select a category using the buttons below:", 
        color=0x9b59b6
    )
    embed.set_footer(text="Click a button to see more options")
    await ctx.send(embed=embed, view=MainMenu())

@bot.command(name='commands', aliases=['cmds'])  # Убрал 'help' из алиасов
async def list_commands(ctx):
    """Show all available commands"""
    embed = discord.Embed(title="📋 All Commands", color=0x3498db)
    
    embed.add_field(
        name="Main", 
        value="`!menu` - Open main menu\n`!commands` - This list", 
        inline=False
    )
    
    # Group RP commands by category
    rp_by_category = {}
    for cmd_name, cmd_data in rp_actions.items():
        cat_name = cmd_data["category_name"]
        if cat_name not in rp_by_category:
            rp_by_category[cat_name] = []
        rp_by_category[cat_name].append(f"`!{cmd_name}`")
    
    for cat_name, commands_list in rp_by_category.items():
        embed.add_field(
            name=cat_name,
            value=", ".join(commands_list[:6]) + (f" and {len(commands_list)-6} more..." if len(commands_list) > 6 else ""),
            inline=False
        )
    
    embed.add_field(
        name="Level System", 
        value="`!profile [@user]` - View profile\n`!top` - Leaderboard\n`!level` - Your level", 
        inline=False
    )
    
    embed.add_field(
        name="Utilities", 
        value="`!ping` - Bot latency\n`!server` - Server info\n`!avatar [@user]` - Get avatar\n`!random [min] [max]` - Random number\n`!coinflip` - Flip a coin\n`!dice` - Roll dice\n`!choose` - Choose option\n`!8ball` - Magic 8-ball", 
        inline=False
    )
    
    embed.set_footer(text=f"Total commands: {len(bot.commands) + len(rp_actions)}")
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    start_time = datetime.datetime.now()
    message = await ctx.send("🏓 Measuring ping...")
    end_time = datetime.datetime.now()
    
    latency = round(bot.latency * 1000)
    response_time = round((end_time - start_time).total_seconds() * 1000)
    
    embed = discord.Embed(title="🏓 Pong!", color=0x00ff00)
    embed.add_field(name="API Latency", value=f"**{latency}ms**", inline=True)
    embed.add_field(name="Response Time", value=f"**{response_time}ms**", inline=True)
    embed.set_footer(text=f"Requested by: {ctx.author.display_name}")
    
    await message.edit(content=None, embed=embed)

@bot.command(name='server', aliases=['serverinfo', 'guild'])
async def server_info(ctx):
    """Show server information"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"📊 Server Information: {guild.name}",
        color=0x3498db
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="📅 Created", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
    embed.add_field(name="✨ Boosts", value=guild.premium_subscription_count, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='user', aliases=['userinfo', 'whois'])
async def user_info(ctx, member: discord.Member = None):
    """Show user information"""
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"👤 User Information: {member.display_name}",
        color=member.color if member.color.value != 0 else 0x3498db
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="🆔 User ID", value=member.id, inline=True)
    embed.add_field(name="📛 Name", value=f"{member.name}#{member.discriminator}" if hasattr(member, 'discriminator') else member.name, inline=True)
    embed.add_field(name="📅 Joined Server", value=member.joined_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="📅 Joined Discord", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)
    embed.add_field(name="🎨 Roles", value=len(member.roles[1:]), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='avatar', aliases=['av', 'pfp'])
async def avatar(ctx, member: discord.Member = None):
    """Show user avatar"""
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"🖼️ Avatar: {member.display_name}",
        color=member.color if member.color.value != 0 else 0x3498db
    )
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='random', aliases=['rand', 'roll'])
async def random_number(ctx, min_val: int = 1, max_val: int = 100):
    """Generate a random number"""
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    result = random.randint(min_val, max_val)
    
    embed = discord.Embed(
        title="🎲 Random Number",
        description=f"From **{min_val}** to **{max_val}**\n\n**Result: {result}**",
        color=0x9b59b6
    )
    
    await ctx.send(embed=embed)

@bot.command(name='coinflip', aliases=['coin'])
async def coinflip(ctx):
    """Flip a coin"""
    result = random.choice(["Heads", "Tails"])
    
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"**Result: {result}**",
        color=0xffd700
    )
    
    await ctx.send(embed=embed)

@bot.command(name='dice', aliases=['roll_dice'])
async def dice(ctx, sides: int = 6):
    """Roll a dice"""
    if sides < 2:
        await ctx.send("❌ Dice must have at least 2 sides!")
        return
    
    result = random.randint(1, sides)
    
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"🎯 **{result}** (1-{sides})",
        color=0x9b59b6
    )
    
    await ctx.send(embed=embed)

@bot.command(name='choose')
async def choose(ctx, *options):
    """Choose between options (separate with spaces)"""
    if len(options) < 2:
        await ctx.send("❌ Please provide at least 2 options! Example: `!choose pizza burger`")
        return
    
    choice = random.choice(options)
    
    embed = discord.Embed(
        title="🤔 I Choose...",
        description=f"**{choice}**",
        color=0x3498db
    )
    
    await ctx.send(embed=embed)

@bot.command(name='8ball', aliases=['magicball'])
async def magic_8ball(ctx, *, question):
    """Ask the magic 8-ball a question"""
    responses = [
        "🎱 It is certain.", "🎱 It is decidedly so.", "🎱 Without a doubt.",
        "🎱 Yes - definitely.", "🎱 You may rely on it.", "🎱 As I see it, yes.",
        "🎱 Most likely.", "🎱 Outlook good.", "🎱 Yes.", "🎱 Signs point to yes.",
        "🎱 Reply hazy, try again.", "🎱 Ask again later.", "🎱 Better not tell you now.",
        "🎱 Cannot predict now.", "🎱 Concentrate and ask again.",
        "🎱 Don't count on it.", "🎱 My reply is no.", "🎱 My sources say no.",
        "🎱 Outlook not so good.", "🎱 Very doubtful."
    ]
    
    embed = discord.Embed(
        title="🎱 Magic 8-Ball",
        color=0x9b59b6
    )
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=random.choice(responses), inline=False)
    
    await ctx.send(embed=embed)

# --- PROFILE AND LEVEL COMMANDS ---

@bot.command(name='profile', aliases=['p'])
async def profile(ctx, member: discord.Member = None):
    """Show user profile with level info"""
    if member is None:
        member = ctx.author
    
    user_id = str(member.id)
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_time": 0}
    
    data = user_levels[user_id]
    current_level = data["level"]
    current_xp = data["xp"]
    xp_for_next = 100 * (current_level ** 2)
    progress = (current_xp / xp_for_next) * 100 if xp_for_next > 0 else 0
    
    # Create progress bar
    progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
    
    embed = discord.Embed(
        title=f"📊 Profile: {member.display_name}",
        color=member.color if member.color.value != 0 else 0xffd700
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="Level", value=f"**{current_level}**", inline=True)
    embed.add_field(name="Experience", value=f"{current_xp}/{xp_for_next}", inline=True)
    embed.add_field(name="Progress", value=f"{progress_bar} {progress:.1f}%", inline=False)
    embed.add_field(name="Messages", value=data["messages"], inline=True)
    embed.add_field(name="Voice Time", value=f"{data['voice_time']} min", inline=True)
    embed.add_field(name="Rank", value=f"#{await get_rank(user_id)}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='level', aliases=['lvl'])
async def level(ctx):
    """Show your current level"""
    await profile(ctx, ctx.author)

@bot.command(name='top', aliases=['leaderboard', 'lb'])
async def top(ctx):
    """Show level leaderboard"""
    # Sort users by level and XP
    sorted_users = sorted(user_levels.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]
    
    embed = discord.Embed(
        title="🏆 Leaderboard",
        description="**Top 10 Users by Level:**",
        color=0xffd700
    )
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = f"Unknown User"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        embed.add_field(
            name=f"{medal} {i}. {name}", 
            value=f"Level: **{data['level']}** | XP: {data['xp']}", 
            inline=False
        )
    
    await ctx.send(embed=embed)

async def get_rank(user_id):
    """Get user rank"""
    sorted_users = sorted(user_levels.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    for i, (uid, _) in enumerate(sorted_users, 1):
        if uid == user_id:
            return i
    return len(sorted_users) + 1

# --- RP COMMANDS (dynamically created) ---

async def send_rp_action(ctx, action_key, target):
    """Helper function for RP actions"""
    if target == ctx.author:
        await ctx.send("❌ You cannot use this action on yourself!")
        return
    
    action_data = rp_actions.get(action_key)
    if not action_data:
        await ctx.send("❌ Action not found!")
        return
    
    message = action_data['text'].format(author=ctx.author.mention, target=target.mention)
    
    embed = discord.Embed(description=message, color=action_data['color'])
    
    # Add random GIF with 50% chance
    if action_data['gifs'] and random.random() < 0.5:
        embed.set_image(url=random.choice(action_data['gifs']))
    
    # Add XP for using RP commands
    user_id = str(ctx.author.id)
    if user_id in user_levels:
        user_levels[user_id]["xp"] += 5
        check_level_up(user_id)
        save_levels(user_levels)
    
    await ctx.send(embed=embed)

# Dynamically create RP commands
for action_name in rp_actions.keys():
    @bot.command(name=action_name)
    async def rp_command(ctx, member: discord.Member = None, action=action_name):
        if member is None:
            await ctx.send(f"❌ Please mention a user! Example: `!{action} @username`")
            return
        await send_rp_action(ctx, action, member)

# --- LEVEL SYSTEM ---

def check_level_up(user_id):
    """Check if user should level up"""
    if user_id not in user_levels:
        return False
    
    data = user_levels[user_id]
    current_level = data["level"]
    current_xp = data["xp"]
    xp_needed = 100 * (current_level ** 2)
    
    if current_xp >= xp_needed:
        data["level"] += 1
        data["xp"] -= xp_needed
        return True
    return False

@bot.event
async def on_message(message):
    """Process messages for XP system"""
    if message.author.bot:
        return
    
    # XP System
    user_id = str(message.author.id)
    current_time = datetime.datetime.now()
    
    # Initialize user data
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_time": 0}
    
    # Anti-spam check (30 seconds cooldown)
    last_time = last_message_time[message.guild.id].get(user_id)
    if not last_time or (current_time - last_time).total_seconds() > 30:
        # Give XP: 10-20 per message
        xp_gain = random.randint(10, 20)
        user_levels[user_id]["xp"] += xp_gain
        user_levels[user_id]["messages"] += 1
        
        # Check level up
        if check_level_up(user_id):
            level = user_levels[user_id]["level"]
            await message.channel.send(f"🎉 {message.author.mention} reached level **{level}**!")
        
        last_message_time[message.guild.id][user_id] = current_time
        save_levels(user_levels)
    
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    """Track voice activity for XP"""
    if member.bot:
        return
    
    user_id = str(member.id)
    
    # Initialize user data
    if user_id not in user_levels:
        user_levels[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_time": 0}
    
    # User joined voice channel
    if after.channel and (not before.channel or before.channel != after.channel):
        voice_timer = asyncio.create_task(voice_xp_timer(member, after.channel))
        member.voice_timer = voice_timer
    
    # User left voice channel
    if before.channel and (not after.channel or before.channel != after.channel):
        if hasattr(member, 'voice_timer'):
            member.voice_timer.cancel()

async def voice_xp_timer(member, channel):
    """Timer for voice XP"""
    try:
        while True:
            await asyncio.sleep(60)  # Every minute
            
            # Check if user is still in voice and not alone
            if member.voice and member.voice.channel == channel:
                if len(channel.members) > 1:
                    user_id = str(member.id)
                    if user_id not in user_levels:
                        user_levels[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_time": 0}
                    
                    # Give XP for voice time
                    user_levels[user_id]["xp"] += 5
                    user_levels[user_id]["voice_time"] += 1
                    
                    # Check level up
                    if check_level_up(user_id):
                        if member.guild.system_channel:
                            await member.guild.system_channel.send(f"🎉 {member.mention} reached level **{user_levels[user_id]['level']}**!")
                    
                    save_levels(user_levels)
            else:
                break
    except asyncio.CancelledError:
        pass

# --- ERROR HANDLERS ---

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Use `!commands` for help.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument. Please check your input.")
    elif isinstance(error, commands.CommandNotFound):
        # Ignore unknown commands
        pass
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} successfully connected!')
    print(f'📊 Servers: {len(bot.guilds)}')
    print(f'🎮 Commands loaded: {len(bot.commands)}')
    print(f'🎭 RP Commands: {len(rp_actions)}')
    print(f'📁 Level data loaded for {len(user_levels)} users')
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="!menu | Level System"
        )
    )

# Run the bot
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get token from environment
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: Token not found!")
        print("🔑 Create a .env file and add:")
        print("DISCORD_TOKEN=your_bot_token_here")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Error: Invalid bot token!")
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
