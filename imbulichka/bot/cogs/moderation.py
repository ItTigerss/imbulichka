import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from config import COLORS, VERIFICATION_ROLE, MUTE_ROLE

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="verify")
    async def verify_command(self, ctx):
        """Get verified role"""
        role = discord.utils.get(ctx.guild.roles, name=VERIFICATION_ROLE)
        
        if not role:
            try:
                role = await ctx.guild.create_role(
                    name=VERIFICATION_ROLE,
                    color=discord.Color.green(),
                    reason="Verification role"
                )
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Error",
                    description="I don't have permission to create roles!",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed)
                return
        
        if role in ctx.author.roles:
            embed = discord.Embed(
                title="ℹ️ Already Verified",
                description="You're already verified!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        try:
            await ctx.author.add_roles(role)
            
            embed = discord.Embed(
                title="✅ Verified!",
                description=f"You now have the **{VERIFICATION_ROLE}** role!",
                color=COLORS["SUCCESS"]
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permission to add roles!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx, amount: int = 10):
        """Clear messages"""
        if amount < 1:
            amount = 1
        if amount > 100:
            amount = 100
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Deleted **{len(deleted) - 1}** messages",
            color=COLORS["SUCCESS"]
        )
        
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_command(self, ctx, member: discord.Member, duration: str = "30m", *, reason="No reason"):
        """Mute a user"""
        mute_role = discord.utils.get(ctx.guild.roles, name=MUTE_ROLE)
        
        if not mute_role:
            try:
                mute_role = await ctx.guild.create_role(
                    name=MUTE_ROLE,
                    color=discord.Color.dark_grey(),
                    reason="Mute role"
                )
                
                # Set permissions
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
                    
            except discord.Forbidden:
                await ctx.send("I can't create mute role!")
                return
        
        # Parse duration
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = duration[-1]
        amount = int(duration[:-1])
        
        if unit not in time_units:
            await ctx.send("Invalid time unit! Use s, m, h, or d.")
            return
        
        seconds = amount * time_units[unit]
        
        try:
            await member.add_roles(mute_role, reason=reason)
            
            embed = discord.Embed(
                title="🔇 User Muted",
                color=COLORS["ERROR"]
            )
            
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Auto unmute
            if seconds > 0:
                await asyncio.sleep(seconds)
                if mute_role in member.roles:
                    await member.remove_roles(mute_role, reason="Mute expired")
                    
        except discord.Forbidden:
            await ctx.send("I can't mute this user!")
    
    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute_command(self, ctx, member: discord.Member):
        """Unmute a user"""
        mute_role = discord.utils.get(ctx.guild.roles, name=MUTE_ROLE)
        
        if not mute_role:
            await ctx.send("No mute role found!")
            return
        
        if mute_role not in member.roles:
            await ctx.send("This user is not muted!")
            return
        
        try:
            await member.remove_roles(mute_role, reason="Unmuted")
            
            embed = discord.Embed(
                title="🔊 User Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=COLORS["SUCCESS"]
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("I can't unmute this user!")
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason="No reason"):
        """Kick a user"""
        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 User Kicked",
                color=COLORS["ERROR"]
            )
            
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("I can't kick this user!")
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason="No reason"):
        """Ban a user"""
        try:
            await member.ban(reason=reason, delete_message_days=0)
            
            embed = discord.Embed(
                title="🔨 User Banned",
                color=COLORS["ERROR"]
            )
            
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("I can't ban this user!")
    
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_command(self, ctx, member: discord.Member, *, reason="No reason"):
        """Warn a user"""
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """INSERT INTO warnings (user_id, guild_id, moderator_id, reason) 
                VALUES (?, ?, ?, ?)""",
                (member.id, ctx.guild.id, ctx.author.id, reason)
            )
            
            await cursor.execute(
                "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?",
                (member.id, ctx.guild.id)
            )
            warning_count = (await cursor.fetchone())[0]
            
            await self.bot.db.commit()
        
        embed = discord.Embed(
            title="⚠️ Warning Issued",
            color=COLORS["WARNING"]
        )
        
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Total Warnings", value=str(warning_count), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="warnings")
    async def warnings_command(self, ctx, member: discord.Member = None):
        """Show user warnings"""
        member = member or ctx.author
        
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """SELECT reason, created_at, moderator_id 
                FROM warnings WHERE user_id = ? AND guild_id = ? 
                ORDER BY created_at DESC LIMIT 5""",
                (member.id, ctx.guild.id)
            )
            warnings = await cursor.fetchall()
            
            await cursor.execute(
                "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?",
                (member.id, ctx.guild.id)
            )
            warning_count = (await cursor.fetchone())[0]
        
        if warning_count == 0:
            embed = discord.Embed(
                title="⚠️ Warnings",
                description=f"{member.name} has no warnings.",
                color=COLORS["SUCCESS"]
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⚠️ {member.name}'s Warnings",
            description=f"Total: **{warning_count}** warnings",
            color=COLORS["WARNING"]
        )
        
        for i, (reason, created_at, mod_id) in enumerate(warnings, 1):
            moderator = ctx.guild.get_member(mod_id)
            mod_name = moderator.name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {reason}\n**Moderator:** {mod_name}\n**Date:** {created_at[:10]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
