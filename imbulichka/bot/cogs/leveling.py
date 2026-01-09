import discord
from discord.ext import commands
import random
import math
from datetime import datetime
from config import COLORS
import asyncio

class LevelingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cooldown = {}
        self.voice_tracking = {}  # Для отслеживания времени в голосовых каналах
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice channel time"""
        if member.bot:
            return
        
        guild_id = member.guild.id
        user_id = member.id
        
        # User joined a voice channel
        if before.channel is None and after.channel is not None:
            self.voice_tracking[user_id] = {
                'guild_id': guild_id,
                'join_time': datetime.now(),
                'channel': after.channel
            }
        
        # User left a voice channel
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_tracking:
                data = self.voice_tracking[user_id]
                time_spent = (datetime.now() - data['join_time']).total_seconds() / 60  # в минутах
                
                if time_spent >= 1:  # Минимум 1 минута
                    await self.add_voice_xp(user_id, guild_id, int(time_spent))
                
                del self.voice_tracking[user_id]
        
        # User switched channels
        elif before.channel != after.channel and after.channel is not None:
            if user_id in self.voice_tracking:
                data = self.voice_tracking[user_id]
                time_spent = (datetime.now() - data['join_time']).total_seconds() / 60
                
                if time_spent >= 1:
                    await self.add_voice_xp(user_id, guild_id, int(time_spent))
                
                # Start tracking in new channel
                self.voice_tracking[user_id] = {
                    'guild_id': guild_id,
                    'join_time': datetime.now(),
                    'channel': after.channel
                }
    
    async def add_voice_xp(self, user_id, guild_id, minutes):
        """Add XP for voice time"""
        xp_gain = minutes * 12  # 12 XP за минуту
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                "SELECT xp, level, voice_time FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            result = await cursor.fetchone()
            
            if result:
                current_xp, current_level, current_voice_time = result
                new_xp = current_xp + xp_gain
                new_voice_time = current_voice_time + minutes
                
                # Check level up
                required_xp = 100 * (current_level ** 1.5)
                
                if new_xp >= required_xp:
                    new_level = current_level + 1
                    remaining_xp = new_xp - required_xp
                    reward = new_level * 100
                    
                    await cursor.execute(
                        """UPDATE users 
                        SET xp = ?, level = ?, voice_time = ?, 
                            total_xp = total_xp + ?, coins = coins + ? 
                        WHERE user_id = ? AND guild_id = ?""",
                        (remaining_xp, new_level, new_voice_time, xp_gain, reward, user_id, guild_id)
                    )
                    
                    # Send level up message
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        member = guild.get_member(user_id)
                        if member:
                            channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
                            if channel:
                                embed = discord.Embed(
                                    title="🎉 Level Up!",
                                    description=f"{member.mention} reached **level {new_level}**!",
                                    color=COLORS["SUCCESS"]
                                )
                                embed.add_field(name="Reward", value=f"🎁 {reward} coins")
                                embed.add_field(name="Source", value="Voice Activity")
                                await channel.send(embed=embed)
                else:
                    await cursor.execute(
                        """UPDATE users 
                        SET xp = xp + ?, voice_time = voice_time + ?, 
                            total_xp = total_xp + ? 
                        WHERE user_id = ? AND guild_id = ?""",
                        (xp_gain, minutes, xp_gain, user_id, guild_id)
                    )
            else:
                # Create new user
                await cursor.execute(
                    """INSERT INTO users (user_id, guild_id, xp, voice_time) 
                    VALUES (?, ?, ?, ?)""",
                    (user_id, guild_id, xp_gain, minutes)
                )
            
            await self.bot.db.commit()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Add XP for messages"""
        if message.author.bot or not message.guild:
            return
        
        # Check cooldown
        user_key = f"{message.author.id}_{message.guild.id}"
        current_time = datetime.now().timestamp()
        
        if user_key in self.message_cooldown:
            if current_time - self.message_cooldown[user_key] < 60:
                return
        
        self.message_cooldown[user_key] = current_time
        
        # Add XP
        await self.add_message_xp(message.author.id, message.guild.id)
        
        # Update server stats
        await self.bot.update_server_stats(message.guild.id, messages=1)
    
    async def add_message_xp(self, user_id, guild_id):
        """Add XP for a message"""
        xp_gain = random.randint(15, 25)
        
        async with self.bot.db.cursor() as cursor:
            # Get current data
            await cursor.execute(
                "SELECT xp, level, coins, messages FROM users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            result = await cursor.fetchone()
            
            if result is None:
                # Create new user
                await cursor.execute(
                    """INSERT INTO users (user_id, guild_id, xp, level, messages, coins) 
                    VALUES (?, ?, ?, 1, 1, 500)""",
                    (user_id, guild_id, xp_gain)
                )
            else:
                current_xp, current_level, coins, messages = result
                new_xp = current_xp + xp_gain
                
                # Check level up
                required_xp = 100 * (current_level ** 1.5)
                
                if new_xp >= required_xp:
                    new_level = current_level + 1
                    remaining_xp = new_xp - required_xp
                    reward = new_level * 100
                    
                    await cursor.execute(
                        """UPDATE users 
                        SET xp = ?, level = ?, messages = messages + 1, 
                            total_xp = total_xp + ?, coins = coins + ? 
                        WHERE user_id = ? AND guild_id = ?""",
                        (remaining_xp, new_level, xp_gain, reward, user_id, guild_id)
                    )
                    
                    # Send level up message
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        member = guild.get_member(user_id)
                        if member:
                            channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
                            if channel:
                                embed = discord.Embed(
                                    title="🎉 Level Up!",
                                    description=f"{member.mention} reached **level {new_level}**!",
                                    color=COLORS["SUCCESS"]
                                )
                                embed.add_field(name="Reward", value=f"🎁 {reward} coins")
                                embed.set_thumbnail(url=member.avatar.url)
                                await channel.send(embed=embed)
                else:
                    await cursor.execute(
                        """UPDATE users 
                        SET xp = xp + ?, messages = messages + 1, 
                            total_xp = total_xp + ? 
                        WHERE user_id = ? AND guild_id = ?""",
                        (xp_gain, xp_gain, user_id, guild_id)
                    )
            
            await self.bot.db.commit()
    
    @commands.command(name="rank", aliases=["level", "profile"])
    async def rank_command(self, ctx, member: discord.Member = None):
        """Show user rank and profile"""
        member = member or ctx.author
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT xp, level, messages, voice_time, total_xp, coins 
                FROM users WHERE user_id = ? AND guild_id = ?""",
                (member.id, ctx.guild.id)
            )
            result = await cursor.fetchone()
            
            if result is None:
                embed = discord.Embed(
                    title="📊 Profile",
                    description=f"{member.mention} doesn't have stats yet!",
                    color=COLORS["INFO"]
                )
                await ctx.send(embed=embed)
                return
            
            xp, level, messages, voice_time, total_xp, coins = result
            
            # Get rank position
            await cursor.execute(
                """SELECT user_id FROM users 
                WHERE guild_id = ? ORDER BY level DESC, total_xp DESC""",
                (ctx.guild.id,)
            )
            leaderboard = await cursor.fetchall()
            rank = next((i+1 for i, (uid,) in enumerate(leaderboard) if uid == member.id), 1)
            
            # Calculate progress
            required_xp = 100 * (level ** 1.5)
            progress_percent = min((xp / required_xp) * 100, 100)
            
            # Create progress bar
            filled = math.floor(progress_percent / 100 * 20)
            progress_bar = "█" * filled + "░" * (20 - filled)
            
            # Format voice time
            voice_hours = voice_time // 60
            voice_minutes = voice_time % 60
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Profile • {member.name}",
                color=COLORS["PRIMARY"]
            )
            
            embed.set_thumbnail(url=member.avatar.url)
            
            embed.add_field(
                name=f"📈 Level {level} • Rank #{rank}",
                value=f"**{xp:,}** / **{int(required_xp):,} XP**",
                inline=False
            )
            
            embed.add_field(
                name="Progress",
                value=f"```{progress_bar} {progress_percent:.1f}%```",
                inline=False
            )
            
            embed.add_field(
                name="💬 Messages",
                value=f"```{messages:,}```",
                inline=True
            )
            
            embed.add_field(
                name="🎤 Voice Time",
                value=f"```{voice_hours}h {voice_minutes}m```",
                inline=True
            )
            
            embed.add_field(
                name="💰 Coins",
                value=f"```{coins:,}```",
                inline=True
            )
            
            # Calculate activity score
            activity_score = messages + (voice_time // 10)
            embed.add_field(
                name="📊 Activity Score",
                value=f"```{activity_score:,}```",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.command(name="leaderboard", aliases=["lb", "top", "leaders"])
    async def leaderboard_command(self, ctx, type: str = "level"):
        """Show leaderboard (level/messages/voice/coins/activity)"""
        type = type.lower()
        
        if type not in ["level", "messages", "voice", "coins", "activity"]:
            type = "level"
        
        async with self.bot.db.cursor() as cursor:
            if type == "level":
                await cursor.execute(
                    """SELECT user_id, level, total_xp 
                    FROM users WHERE guild_id = ? 
                    ORDER BY level DESC, total_xp DESC LIMIT 10""",
                    (ctx.guild.id,)
                )
            elif type == "messages":
                await cursor.execute(
                    """SELECT user_id, messages 
                    FROM users WHERE guild_id = ? 
                    ORDER BY messages DESC LIMIT 10""",
                    (ctx.guild.id,)
                )
            elif type == "voice":
                await cursor.execute(
                    """SELECT user_id, voice_time 
                    FROM users WHERE guild_id = ? 
                    ORDER BY voice_time DESC LIMIT 10""",
                    (ctx.guild.id,)
                )
            elif type == "coins":
                await cursor.execute(
                    """SELECT user_id, coins 
                    FROM users WHERE guild_id = ? 
                    ORDER BY coins DESC LIMIT 10""",
                    (ctx.guild.id,)
                )
            elif type == "activity":
                await cursor.execute(
                    """SELECT user_id, messages, voice_time 
                    FROM users WHERE guild_id = ? 
                    ORDER BY (messages + (voice_time / 10)) DESC LIMIT 10""",
                    (ctx.guild.id,)
                )
            
            results = await cursor.fetchall()
            
            if not results:
                embed = discord.Embed(
                    title="🏆 Leaderboard",
                    description="No data yet!",
                    color=COLORS["INFO"]
                )
                await ctx.send(embed=embed)
                return
            
            # Create embed
            titles = {
                "level": "🏆 Level Leaderboard",
                "messages": "💬 Messages Leaderboard",
                "voice": "🎤 Voice Time Leaderboard",
                "coins": "💰 Coin Leaderboard",
                "activity": "📊 Activity Leaderboard"
            }
            
            embed = discord.Embed(
                title=titles.get(type, "🏆 Leaderboard"),
                color=COLORS["SUCCESS"]
            )
            
            leaderboard_text = ""
            for i, row in enumerate(results, 1):
                user_id = row[0]
                member = ctx.guild.get_member(user_id)
                username = member.name if member else f"User {user_id}"
                
                if type == "level":
                    level, xp = row[1], row[2]
                    leaderboard_text += f"**{i}. {username}** - Level {level} ({xp:,} XP)\n"
                elif type == "messages":
                    messages = row[1]
                    leaderboard_text += f"**{i}. {username}** - {messages:,} messages\n"
                elif type == "voice":
                    voice_time = row[1]
                    hours = voice_time // 60
                    minutes = voice_time % 60
                    leaderboard_text += f"**{i}. {username}** - {hours}h {minutes}m\n"
                elif type == "coins":
                    coins = row[1]
                    leaderboard_text += f"**{i}. {username}** - {coins:,} coins\n"
                elif type == "activity":
                    messages, voice_time = row[1], row[2]
                    activity_score = messages + (voice_time // 10)
                    leaderboard_text += f"**{i}. {username}** - Score: {activity_score:,}\n"
            
            embed.description = leaderboard_text
            embed.set_footer(text=f"Total members: {ctx.guild.member_count}")
            
            await ctx.send(embed=embed)
    
    @commands.command(name="stats")
    async def stats_command(self, ctx):
        """Show server statistics"""
        await ctx.invoke(self.bot.get_command("serverstats"))
    
    @commands.command(name="xpinfo")
    async def xpinfo_command(self, ctx, member: discord.Member = None):
        """Show XP details"""
        member = member or ctx.author
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                "SELECT xp, level, total_xp FROM users WHERE user_id = ? AND guild_id = ?",
                (member.id, ctx.guild.id)
            )
            result = await cursor.fetchone()
            
            if not result:
                await ctx.send(f"{member.mention} doesn't have XP yet!")
                return
            
            xp, level, total_xp = result
            
            embed = discord.Embed(
                title=f"✨ XP Info • {member.name}",
                color=COLORS["INFO"]
            )
            
            embed.set_thumbnail(url=member.avatar.url)
            
            embed.add_field(name="Current XP", value=f"{xp:,}", inline=True)
            embed.add_field(name="Level", value=f"{level}", inline=True)
            embed.add_field(name="Total XP", value=f"{total_xp:,}", inline=True)
            
            # Calculate next level
            required_xp = 100 * (level ** 1.5)
            needed = max(0, required_xp - xp)
            xp_per_message = "15-25"
            estimated_messages = needed // 20
            
            embed.add_field(
                name="Next Level",
                value=f"{needed:,} XP needed\n~{estimated_messages} messages ({xp_per_message} XP/msg)",
                inline=False
            )
            
            # XP sources
            embed.add_field(
                name="📈 XP Sources",
                value="```💬 Messages: 15-25 XP (60s cooldown)\n🎤 Voice: 12 XP/minute\n🎉 Level Up Bonus: Level × 100 coins```",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @commands.command(name="levelinfo")
    async def levelinfo_command(self, ctx, member: discord.Member = None):
        """Show level information"""
        await self.rank_command(ctx, member)

async def setup(bot):
    await bot.add_cog(LevelingCog(bot))
