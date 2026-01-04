import discord
from discord.ext import commands
import random
import json
import os
import sqlite3
import time
from bot.database import db
from config import Config

class Cards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cards_data = self.load_cards()
        self.card_cooldowns = {}
    
    def load_cards(self):
        if os.path.exists("data/cards.json"):
            with open("data/cards.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "cards": [
                {"id": "001", "name": "Starshine Orb", "rarity": "common", "value": 10},
                {"id": "002", "name": "Moonlight Crystal", "rarity": "rare", "value": 50},
                {"id": "003", "name": "Galaxy Fragment", "rarity": "epic", "value": 200},
                {"id": "004", "name": "Cosmic Singularity", "rarity": "legendary", "value": 1000},
                {"id": "005", "name": "Solar Flare", "rarity": "common", "value": 15},
                {"id": "006", "name": "Nebula Dust", "rarity": "common", "value": 12},
                {"id": "007", "name": "Comet Tail", "rarity": "rare", "value": 60},
                {"id": "008", "name": "Black Hole Core", "rarity": "epic", "value": 250},
                {"id": "009", "name": "Supernova Remnant", "rarity": "legendary", "value": 1200}
            ]
        }
    
    @commands.command(name="pack", aliases=["buycard"])
    async def buy_pack(self, ctx):
        """Buy a card pack for 1000 coins"""
        user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if not user_data:
            db.create_user(ctx.author.id, ctx.guild.id)
            user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        if user_data['coins'] < Config.CARD_PACK_PRICE:
            await ctx.send(f"You need {Config.CARD_PACK_PRICE} coins to buy a card pack!")
            return
        
        # Deduct coins
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ? AND guild_id = ?",
            (Config.CARD_PACK_PRICE, ctx.author.id, ctx.guild.id)
        )
        
        # Determine rarity
        rand = random.random()
        if rand < 0.6:
            rarity = "common"
        elif rand < 0.85:
            rarity = "rare"
        elif rand < 0.95:
            rarity = "epic"
        else:
            rarity = "legendary"
        
        # Get random card of that rarity
        cards_of_rarity = [c for c in self.cards_data["cards"] if c["rarity"] == rarity]
        if not cards_of_rarity:
            card = {"id": "000", "name": "Mystery Card", "rarity": rarity, "value": 10}
        else:
            card = random.choice(cards_of_rarity)
        
        # Add to collection
        cursor.execute(
            "INSERT INTO user_cards (user_id, card_id, card_name, rarity) VALUES (?, ?, ?, ?)",
            (ctx.author.id, card["id"], card["name"], card["rarity"])
        )
        
        conn.commit()
        conn.close()
        
        # Create embed
        colors = {
            "common": 0x808080,
            "rare": 0x1E90FF,
            "epic": 0x9B59B6,
            "legendary": 0xFFD700
        }
        
        embed = discord.Embed(
            title="🎴 Card Pack Opened!",
            description=f"You got a **{card['name']}**!",
            color=colors.get(rarity, Config.EMBED_COLOR)
        )
        embed.add_field(name="Rarity", value=rarity.title(), inline=True)
        embed.add_field(name="Value", value=f"{card['value']} ⭐", inline=True)
        embed.set_footer(text=f"Remaining coins: {user_data['coins'] - Config.CARD_PACK_PRICE}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="card", aliases=["getcard"])
    async def get_card(self, ctx):
        """Get a free card (2 hour cooldown)"""
        user_id = ctx.author.id
        current_time = time.time()
        
        # Проверка кулдауна (2 часа = 7200 секунд)
        if user_id in self.card_cooldowns:
            if current_time - self.card_cooldowns[user_id] < 7200:
                remaining = 7200 - (current_time - self.card_cooldowns[user_id])
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                await ctx.send(f"⏰ You need to wait {hours}h {minutes}m before searching for cards again!")
                return
        
        user_data = db.get_user(ctx.author.id, ctx.guild.id)
        if not user_data:
            db.create_user(ctx.author.id, ctx.guild.id)
            user_data = db.get_user(ctx.author.id, ctx.guild.id)
        
        # 50% шанс получить карту
        if random.random() < 0.5:
            # Получаем случайную карту
            card = random.choice(self.cards_data["cards"])
            
            # Добавляем в коллекцию
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO user_cards (user_id, card_id, card_name, rarity) VALUES (?, ?, ?, ?)",
                (ctx.author.id, card["id"], card["name"], card["rarity"])
            )
            
            # Добавляем монеты за карту
            coin_reward = card["value"] // 2
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                (coin_reward, ctx.author.id, ctx.guild.id)
            )
            
            conn.commit()
            conn.close()
            
            colors = {
                "common": 0x808080,
                "rare": 0x1E90FF,
                "epic": 0x9B59B6,
                "legendary": 0xFFD700
            }
            
            embed = discord.Embed(
                title="🃏 Free Card Found!",
                description=f"You found a **{card['name']}**!",
                color=colors.get(card["rarity"], Config.EMBED_COLOR)
            )
            embed.add_field(name="Rarity", value=card["rarity"].title(), inline=True)
            embed.add_field(name="Value", value=f"{card['value']} ⭐", inline=True)
            embed.add_field(name="Coin Reward", value=f"+{coin_reward} ⭐", inline=True)
            
        else:
            # Не повезло, но даем немного монет
            coin_reward = random.randint(10, 50)
            
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET coins = coins + ? WHERE user_id = ? AND guild_id = ?",
                (coin_reward, ctx.author.id, ctx.guild.id)
            )
            
            conn.commit()
            conn.close()
            
            embed = discord.Embed(
                title="🃏 Card Search",
                description="You searched for cards but didn't find any rare ones...",
                color=Config.WARNING_COLOR
            )
            embed.add_field(name="Coin Reward", value=f"+{coin_reward} ⭐", inline=True)
        
        # Устанавливаем кулдаун
        self.card_cooldowns[user_id] = current_time
        embed.set_footer(text="Try again in 2 hours!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="collection", aliases=["cards", "mycards"])
    async def show_collection(self, ctx, member: discord.Member = None):
        """Show your card collection"""
        member = member or ctx.author
        
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT card_name, rarity, COUNT(*) as count FROM user_cards WHERE user_id = ? GROUP BY card_id",
            (member.id,)
        )
        cards = cursor.fetchall()
        
        conn.close()
        
        if not cards:
            await ctx.send(f"{member.display_name} doesn't have any cards yet!")
            return
        
        embed = discord.Embed(
            title=f"📚 {member.display_name}'s Collection",
            color=Config.EMBED_COLOR
        )
        
        for card_name, rarity, count in cards[:10]:
            embed.add_field(
                name=f"{card_name} ({rarity.title()})",
                value=f"×{count}",
                inline=True
            )
        
        if len(cards) > 10:
            embed.set_footer(text=f"And {len(cards) - 10} more cards...")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Cards(bot))