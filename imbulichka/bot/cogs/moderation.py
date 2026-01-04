import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from bot.database import db
from bot.utils.embeds import create_embed
from config import Config

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear_command(self, ctx, amount: int = 10):
        """Clear messages"""
        await ctx.channel.purge(limit=amount + 1)
        embed = create_embed(
            title="✅ Messages Cleared",
            description=f"Cleared {amount} messages",
            color=Config.SUCCESS_COLOR
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_command(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member"""
        await member.kick(reason=reason)
        embed = create_embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked",
            color=Config.ERROR_COLOR
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        await ctx.send(embed=embed)
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_command(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member"""
        await member.ban(reason=reason)
        embed = create_embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned",
            color=Config.ERROR_COLOR
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        await ctx.send(embed=embed)
    
    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute_command(self, ctx, member: discord.Member, duration: int = 60, *, reason="No reason provided"):
        """Mute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        
        await member.add_roles(muted_role, reason=reason)
        
        embed = create_embed(
            title="🔇 Member Muted",
            description=f"{member.mention} has been muted for {duration} minutes",
            color=Config.WARNING_COLOR
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        await ctx.send(embed=embed)
        
        # Auto unmute
        await asyncio.sleep(duration * 60)
        await member.remove_roles(muted_role, reason="Mute time expired")
    
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn_command(self, ctx, member: discord.Member, *, reason):
        """Warn a member"""
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                "INSERT INTO warnings (user_id, moderator_id, reason) VALUES (?, ?, ?)",
                (member.id, ctx.author.id, reason)
            )
            await conn.commit()
        
        embed = create_embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned",
            color=Config.WARNING_COLOR
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=ctx.author.mention)
        await ctx.send(embed=embed)
    
    @commands.command(name="warnings")
    async def warnings_command(self, ctx, member: discord.Member):
        """Check member's warnings"""
        async with aiosqlite.connect(db.db_path) as conn:
            async with conn.execute(
                "SELECT * FROM warnings WHERE user_id = ?",
                (member.id,)
            ) as cursor:
                warnings = await cursor.fetchall()
        
        if not warnings:
            await ctx.send(f"{member.mention} has no warnings!")
            return
        
        embed = create_embed(
            title=f"⚠️ Warnings for {member.display_name}",
            color=Config.WARNING_COLOR
        )
        
        for warning in warnings[:5]:
            moderator = ctx.guild.get_member(warning[2])
            mod_name = moderator.display_name if moderator else "Unknown"
            embed.add_field(
                name=f"ID: {warning[0]}",
                value=f"**Reason:** {warning[3]}\n**By:** {mod_name}\n**When:** {warning[4]}",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))