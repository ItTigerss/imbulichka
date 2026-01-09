import discord
from discord.ext import commands
from datetime import datetime
from config import COLORS

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="serverstats")
    async def serverstats_command(self, ctx):
        """Show detailed server statistics"""
        guild = ctx.guild
        
        # Get server stats from database
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                "SELECT total_messages, total_voice_time, total_commands FROM server_stats WHERE guild_id = ?",
                (guild.id,)
            )
            db_stats = await cursor.fetchone()
            
            if db_stats:
                total_messages, total_voice_time, total_commands = db_stats
            else:
                total_messages = total_voice_time = total_commands = 0
        
        # Get user statistics
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT 
                    COUNT(*) as active_users,
                    SUM(messages) as user_messages,
                    SUM(voice_time) as user_voice_time,
                    SUM(total_xp) as total_xp,
                    AVG(level) as avg_level
                FROM users WHERE guild_id = ?""",
                (guild.id,)
            )
            user_stats = await cursor.fetchone()
        
        active_users, user_messages, user_voice_time, total_xp, avg_level = user_stats or (0, 0, 0, 0, 0)
        
        # Calculate voice time in hours
        total_voice_hours = total_voice_time // 60
        total_voice_minutes = total_voice_time % 60
        
        user_voice_hours = (user_voice_time or 0) // 60
        user_voice_minutes = (user_voice_time or 0) % 60
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 {guild.name} Statistics",
            color=COLORS["DARK"]
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Server Overview
        embed.add_field(
            name="🌐 Server Overview",
            value=f"""```
👥 Total Members: {guild.member_count}
📅 Created: {guild.created_at.strftime('%Y-%m-%d')}
📁 Channels: {len(guild.channels)}
🎭 Roles: {len(guild.roles)}
```""",
            inline=False
        )
        
        # Activity Statistics
        embed.add_field(
            name="📈 Activity Statistics",
            value=f"""```
💬 Total Messages: {total_messages:,}
🎤 Total Voice Time: {total_voice_hours}h {total_voice_minutes}m
⚡ Total Commands: {total_commands:,}
```""",
            inline=False
        )
        
        # User Statistics
        embed.add_field(
            name="👤 User Statistics",
            value=f"""```
👥 Active Users: {active_users:,}
💬 User Messages: {user_messages or 0:,}
🎤 User Voice Time: {user_voice_hours}h {user_voice_minutes}m
✨ Total XP: {total_xp or 0:,}
📈 Avg Level: {avg_level or 0:.1f}
```""",
            inline=False
        )
        
        # Top Channels
        text_channels = sorted(guild.text_channels, key=lambda c: len(c.members), reverse=True)[:3]
        voice_channels = sorted(guild.voice_channels, key=lambda c: len(c.members), reverse=True)[:3]
        
        top_text = "\n".join([f"• {c.name} ({len(c.members)} members)" for c in text_channels[:3]])
        top_voice = "\n".join([f"• {c.name} ({len(c.members)} members)" for c in voice_channels[:3]])
        
        embed.add_field(
            name="📢 Top Text Channels",
            value=top_text if top_text else "No data",
            inline=True
        )
        
        embed.add_field(
            name="🎤 Top Voice Channels",
            value=top_voice if top_voice else "No data",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="topchatters")
    async def topchatters_command(self, ctx, limit: int = 10):
        """Show top message senders"""
        if limit > 20:
            limit = 20
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT user_id, messages, level 
                FROM users WHERE guild_id = ? 
                ORDER BY messages DESC LIMIT ?""",
                (ctx.guild.id, limit)
            )
            results = await cursor.fetchall()
        
        if not results:
            embed = discord.Embed(
                title="💬 Top Chatters",
                description="No message data yet!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="💬 Top Chatters",
            description=f"Top {len(results)} message senders",
            color=COLORS["PRIMARY"]
        )
        
        leaderboard_text = ""
        for i, (user_id, messages, level) in enumerate(results, 1):
            member = ctx.guild.get_member(user_id)
            username = member.name if member else f"User {user_id}"
            
            leaderboard_text += f"**{i}. {username}** - {messages:,} messages (Level {level})\n"
        
        embed.description = leaderboard_text
        embed.set_footer(text=f"Total messages in server: {self.bot.server_stats.get(ctx.guild.id, {}).get('total_messages', 0):,}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="voiceleaderboard")
    async def voiceleaderboard_command(self, ctx, limit: int = 10):
        """Show voice time leaderboard"""
        if limit > 20:
            limit = 20
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT user_id, voice_time, level 
                FROM users WHERE guild_id = ? 
                ORDER BY voice_time DESC LIMIT ?""",
                (ctx.guild.id, limit)
            )
            results = await cursor.fetchall()
        
        if not results:
            embed = discord.Embed(
                title="🎤 Voice Time Leaderboard",
                description="No voice time data yet!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🎤 Voice Time Leaderboard",
            description=f"Top {len(results)} voice channel users",
            color=COLORS["SECONDARY"]
        )
        
        leaderboard_text = ""
        for i, (user_id, voice_time, level) in enumerate(results, 1):
            member = ctx.guild.get_member(user_id)
            username = member.name if member else f"User {user_id}"
            
            hours = voice_time // 60
            minutes = voice_time % 60
            
            leaderboard_text += f"**{i}. {username}** - {hours}h {minutes}m (Level {level})\n"
        
        embed.description = leaderboard_text
        
        await ctx.send(embed=embed)
    
    @commands.command(name="mystats")
    async def mystats_command(self, ctx):
        """Show your detailed statistics"""
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT 
                    messages, voice_time, total_xp, level, coins,
                    (SELECT COUNT(*) FROM cards WHERE user_id = ? AND guild_id = ?) as card_count,
                    (SELECT SUM(value) FROM cards WHERE user_id = ? AND guild_id = ?) as card_value
                FROM users WHERE user_id = ? AND guild_id = ?""",
                (ctx.author.id, ctx.guild.id, ctx.author.id, ctx.guild.id, ctx.author.id, ctx.guild.id)
            )
            result = await cursor.fetchone()
            
            if not result:
                await ctx.send("You don't have any statistics yet!")
                return
            
            messages, voice_time, total_xp, level, coins, card_count, card_value = result
            
            # Get rank
            await cursor.execute(
                """SELECT COUNT(*) FROM users 
                WHERE guild_id = ? AND (
                    level > ? OR 
                    (level = ? AND total_xp > ?)
                )""",
                (ctx.guild.id, level, level, total_xp)
            )
            rank = (await cursor.fetchone())[0] + 1
        
        # Calculate percentages
        voice_hours = voice_time // 60
        voice_minutes = voice_time % 60
        
        # Get server stats for comparison
        server_messages = self.bot.server_stats.get(ctx.guild.id, {}).get("total_messages", 1)
        message_percentage = (messages / server_messages * 100) if server_messages > 0 else 0
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 {ctx.author.name}'s Statistics",
            color=COLORS["PRIMARY"]
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url)
        
        # Basic Stats
        embed.add_field(
            name="🏆 Rank & Level",
            value=f"**Rank:** #{rank}\n**Level:** {level}\n**Total XP:** {total_xp:,}",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economy",
            value=f"**Coins:** {coins:,}\n**Cards:** {card_count or 0}\n**Card Value:** {card_value or 0:,}",
            inline=True
        )
        
        # Activity Stats
        embed.add_field(
            name="📈 Activity",
            value=f"""```
Messages: {messages:,}
Voice Time: {voice_hours}h {voice_minutes}m
Message %: {message_percentage:.1f}%
```""",
            inline=False
        )
        
        # Achievements
        achievements = []
        if messages >= 1000:
            achievements.append("💬 Chat Master (1000+ messages)")
        if voice_time >= 1000:  # ~16.5 hours
            achievements.append("🎤 Voice Veteran")
        if level >= 10:
            achievements.append("🏆 Level 10+")
        if card_count and card_count >= 10:
            achievements.append("🃏 Card Collector")
        
        if achievements:
            embed.add_field(
                name="🏅 Achievements",
                value="\n".join(achievements),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar", aliases=["ava"])
    async def avatar_command(self, ctx, member: discord.Member = None):
        """Show user avatar"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.name}'s Avatar",
            color=member.color or COLORS["PRIMARY"]
        )
        embed.set_image(url=member.avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo")
    async def serverinfo_command(self, ctx):
        """Show server information"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=COLORS["INFO"]
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        
        embed.add_field(
            name="👥 Members", 
            value=f"Total: {guild.member_count}", 
            inline=True
        )
        
        embed.add_field(
            name="📁 Channels", 
            value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}", 
            inline=True
        )
        
        embed.add_field(name="🎭 Roles", value=str(len(guild.roles)), inline=True)
        
        if guild.description:
            embed.add_field(name="📝 Description", value=guild.description, inline=False)
        
        # Add server stats
        server_stats = self.bot.server_stats.get(guild.id, {})
        if server_stats:
            total_messages = server_stats.get("total_messages", 0)
            total_commands = server_stats.get("total_commands", 0)
            
            embed.add_field(
                name="📊 Activity",
                value=f"Messages: {total_messages:,}\nCommands: {total_commands:,}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="userinfo", aliases=["user"])
    async def userinfo_command(self, ctx, member: discord.Member = None):
        """Show user information"""
        member = member or ctx.author
        
        status_emojis = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        roles = [role.mention for role in member.roles[1:]]
        roles_text = ", ".join(roles) if roles else "No roles"
        
        # Get user stats
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                "SELECT level, messages, voice_time, coins FROM users WHERE user_id = ? AND guild_id = ?",
                (member.id, ctx.guild.id)
            )
            user_stats = await cursor.fetchone()
        
        embed = discord.Embed(
            title=f"👤 {member.name}",
            color=member.color or COLORS["PRIMARY"]
        )
        
        embed.set_thumbnail(url=member.avatar.url)
        
        embed.add_field(name="📛 Name", value=member.name, inline=True)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        
        embed.add_field(
            name="📅 Account Created", 
            value=member.created_at.strftime("%Y-%m-%d"), 
            inline=False
        )
        
        if member.joined_at:
            embed.add_field(
                name="📅 Joined Server", 
                value=member.joined_at.strftime("%Y-%m-%d"), 
                inline=False
            )
        
        embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(
            name="🚦 Status", 
            value=f"{status_emojis.get(member.status, '⚫')} {str(member.status).title()}", 
            inline=True
        )
        
        # Add stats if available
        if user_stats:
            level, messages, voice_time, coins = user_stats
            voice_hours = voice_time // 60
            voice_minutes = voice_time % 60
            
            embed.add_field(
                name="📊 Statistics",
                value=f"""```
Level: {level}
Messages: {messages:,}
Voice Time: {voice_hours}h {voice_minutes}m
Coins: {coins:,}
```""",
                inline=False
            )
        
        if len(roles_text) < 1024:
            embed.add_field(name="🏷️ Roles", value=roles_text, inline=False)
        else:
            embed.add_field(name="🏷️ Roles", value=f"{len(roles)} roles", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="uptime")
    async def uptime_command(self, ctx):
        """Show bot uptime"""
        uptime = datetime.now() - self.bot.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        time_str = ""
        if days > 0:
            time_str += f"{days}d "
        if hours > 0:
            time_str += f"{hours}h "
        if minutes > 0:
            time_str += f"{minutes}m "
        time_str += f"{seconds}s"
        
        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            color=COLORS["INFO"]
        )
        
        embed.add_field(name="Uptime", value=time_str, inline=False)
        embed.add_field(name="Started", value=self.bot.start_time.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="rolesinfo")
    async def rolesinfo_command(self, ctx):
        """Show server roles"""
        roles = [role for role in ctx.guild.roles if role.name != "@everyone"]
        roles.sort(key=lambda x: x.position, reverse=True)
        
        embed = discord.Embed(
            title=f"🎭 {ctx.guild.name} Roles",
            description=f"Total: {len(roles)} roles",
            color=COLORS["SECONDARY"]
        )
        
        roles_text = ""
        for role in roles[:15]:  # Limit to 15 roles
            roles_text += f"{role.mention} - {len(role.members)} members\n"
        
        if roles_text:
            embed.add_field(name="Roles", value=roles_text, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="membersinfo")
    async def membersinfo_command(self, ctx):
        """Show member statistics"""
        guild = ctx.guild
        
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots
        
        embed = discord.Embed(
            title="👥 Member Statistics",
            color=COLORS["PRIMARY"]
        )
        
        embed.add_field(name="Total", value=str(guild.member_count), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        
        embed.add_field(name="🟢 Online", value=str(online), inline=True)
        embed.add_field(name="🟡 Idle", value=str(idle), inline=True)
        embed.add_field(name="🔴 DND", value=str(dnd), inline=True)
        
        # Add percentage
        if guild.member_count > 0:
            online_percentage = (online / guild.member_count) * 100
            embed.add_field(
                name="📊 Online Percentage",
                value=f"{online_percentage:.1f}% online",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="invitelink")
    async def invitelink_command(self, ctx):
        """Get bot invite link"""
        embed = discord.Embed(
            title="🔗 Invite Bot",
            description="[Click here to invite bot to your server]"
                        "(https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&scope=bot&permissions=8)",
            color=COLORS["SUCCESS"]
        )
        
        embed.add_field(
            name="Required Permissions",
            value="```\n- Send Messages\n- Manage Messages\n- Connect to Voice\n- Speak in Voice\n- Use External Emojis\n- Embed Links\n- Attach Files\n- Read Message History\n- Add Reactions\n```",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesCog(bot))
