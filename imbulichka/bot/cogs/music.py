import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
from collections import deque
from config import COLORS, MUSIC_VOLUME, MAX_QUEUE_SIZE
import re

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=MUSIC_VOLUME):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}
        self.voice_clients = {}
    
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque(maxlen=MAX_QUEUE_SIZE)
        return self.queues[guild_id]
    
    def get_voice_client(self, guild_id):
        return self.voice_clients.get(guild_id)
    
    async def play_next(self, guild):
        queue = self.get_queue(guild.id)
        
        if not queue:
            self.now_playing[guild.id] = None
            return
        
        # Get next song
        source = queue.popleft()
        self.now_playing[guild.id] = source
        
        voice_client = self.get_voice_client(guild.id)
        if not voice_client:
            return
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            
            # Play next song
            fut = asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)
            try:
                fut.result()
            except:
                pass
        
        voice_client.play(source, after=after_playing)
        
        # Send now playing message
        channel = guild.system_channel or next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
        if channel:
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{source.title}**",
                color=0x1DB954  # Spotify green
            )
            
            if source.uploader:
                embed.add_field(name="Uploader", value=source.uploader, inline=True)
            
            if source.duration:
                minutes, seconds = divmod(source.duration, 60)
                embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
            
            if source.thumbnail:
                embed.set_thumbnail(url=source.thumbnail)
            
            embed.set_footer(text=f"Queue: {len(queue)} songs")
            
            await channel.send(embed=embed)
    
    @commands.command(name="play", aliases=["p"])
    async def play_command(self, ctx, *, query: str):
        """Play a song from YouTube"""
        # Check if user is in voice channel
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Error",
                description="You need to be in a voice channel!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check permissions
        if not voice_channel.permissions_for(ctx.guild.me).connect:
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permission to join your voice channel!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
            return
        
        # Join voice channel if not already connected
        voice_client = self.get_voice_client(ctx.guild.id)
        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await voice_channel.connect()
                self.voice_clients[ctx.guild.id] = voice_client
            except discord.ClientException:
                embed = discord.Embed(
                    title="❌ Error",
                    description="I'm already connected to a voice channel!",
                    color=COLORS["ERROR"]
                )
                await ctx.send(embed=embed)
                return
        
        # Show searching message
        embed = discord.Embed(
            title="🔍 Searching...",
            description=f"Searching for: `{query}`",
            color=COLORS["INFO"]
        )
        search_msg = await ctx.send(embed=embed)
        
        try:
            # Extract URL from query (if it's a URL)
            if not query.startswith(('http://', 'https://')):
                query = f"ytsearch:{query}"
            
            # Get audio source
            source = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            
            # Add to queue
            queue = self.get_queue(ctx.guild.id)
            queue.append(source)
            
            # Update search message
            embed.title = "✅ Added to Queue"
            embed.description = f"**{source.title}**"
            embed.color = COLORS["SUCCESS"]
            
            if source.uploader:
                embed.add_field(name="Uploader", value=source.uploader, inline=True)
            
            if source.duration:
                minutes, seconds = divmod(source.duration, 60)
                embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
            
            embed.add_field(name="Position in queue", value=f"#{len(queue)}", inline=True)
            
            await search_msg.edit(embed=embed)
            
            # Start playing if nothing is playing
            if not voice_client.is_playing():
                await self.play_next(ctx.guild)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not play the song: {str(e)}",
                color=COLORS["ERROR"]
            )
            await search_msg.edit(embed=embed)
    
    @commands.command(name="pause")
    async def pause_command(self, ctx):
        """Pause the current song"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="No music is playing!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        if voice_client.is_paused():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="Music is already paused!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_client.pause()
        
        embed = discord.Embed(
            title="⏸️ Music Paused",
            color=COLORS["WARNING"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="resume")
    async def resume_command(self, ctx):
        """Resume paused music"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client or not voice_client.is_paused():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="Music is not paused!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_client.resume()
        
        embed = discord.Embed(
            title="▶️ Music Resumed",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="skip")
    async def skip_command(self, ctx):
        """Skip the current song"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="No music is playing!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_client.stop()
        
        embed = discord.Embed(
            title="⏭️ Song Skipped",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="stop")
    async def stop_command(self, ctx):
        """Stop music and clear queue"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="No music is playing!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        # Clear queue
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        
        # Stop playing
        voice_client.stop()
        
        embed = discord.Embed(
            title="⏹️ Music Stopped",
            description="Queue has been cleared.",
            color=COLORS["ERROR"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="queue", aliases=["q"])
    async def queue_command(self, ctx):
        """Show the current queue"""
        queue = self.get_queue(ctx.guild.id)
        
        if not queue:
            embed = discord.Embed(
                title="🎵 Music Queue",
                description="Queue is empty!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        # Show now playing
        now_playing = self.now_playing.get(ctx.guild.id)
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=0x1DB954
        )
        
        if now_playing:
            embed.add_field(
                name="▶️ Now Playing",
                value=f"**{now_playing.title}**",
                inline=False
            )
        
        # Show next 10 songs in queue
        queue_text = ""
        for i, song in enumerate(list(queue)[:10], 1):
            duration = f" ({song.duration//60}:{song.duration%60:02d})" if song.duration else ""
            queue_text += f"{i}. **{song.title}**{duration}\n"
        
        if queue_text:
            embed.add_field(
                name=f"Up Next ({len(queue)} songs)",
                value=queue_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying_command(self, ctx):
        """Show the currently playing song"""
        now_playing = self.now_playing.get(ctx.guild.id)
        
        if not now_playing:
            embed = discord.Embed(
                title="🎵 Now Playing",
                description="Nothing is playing!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{now_playing.title}**",
            color=0x1DB954
        )
        
        if now_playing.uploader:
            embed.add_field(name="Uploader", value=now_playing.uploader, inline=True)
        
        if now_playing.duration:
            minutes, seconds = divmod(now_playing.duration, 60)
            embed.add_field(name="Duration", value=f"{minutes}:{seconds:02d}", inline=True)
        
        if now_playing.thumbnail:
            embed.set_thumbnail(url=now_playing.thumbnail)
        
        queue = self.get_queue(ctx.guild.id)
        embed.set_footer(text=f"Queue: {len(queue)} songs")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="volume")
    async def volume_command(self, ctx, volume: int = None):
        """Set volume (1-100)"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="ℹ️ Info",
                description="No music is playing!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        if volume is None:
            current_volume = int(voice_client.source.volume * 100)
            embed = discord.Embed(
                title="🔊 Volume",
                description=f"Current volume: **{current_volume}%**",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        if volume < 1 or volume > 100:
            embed = discord.Embed(
                title="❌ Error",
                description="Volume must be between 1 and 100!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_client.source.volume = volume / 100
        
        embed = discord.Embed(
            title="🔊 Volume Set",
            description=f"Volume set to **{volume}%**",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        """Shuffle the queue"""
        queue = self.get_queue(ctx.guild.id)
        
        if len(queue) < 2:
            embed = discord.Embed(
                title="ℹ️ Info",
                description="Need at least 2 songs in queue to shuffle!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        import random
        queue_list = list(queue)
        random.shuffle(queue_list)
        self.queues[ctx.guild.id] = deque(queue_list, maxlen=MAX_QUEUE_SIZE)
        
        embed = discord.Embed(
            title="🔀 Queue Shuffled",
            description=f"Shuffled {len(queue_list)} songs!",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="clearqueue")
    async def clearqueue_command(self, ctx):
        """Clear the music queue"""
        queue = self.get_queue(ctx.guild.id)
        
        if not queue:
            embed = discord.Embed(
                title="ℹ️ Info",
                description="Queue is already empty!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        queue.clear()
        
        embed = discord.Embed(
            title="🗑️ Queue Cleared",
            description="Music queue has been cleared!",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="join")
    async def join_command(self, ctx):
        """Join your voice channel"""
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Error",
                description="You need to be in a voice channel!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
            return
        
        voice_channel = ctx.author.voice.channel
        
        try:
            voice_client = await voice_channel.connect()
            self.voice_clients[ctx.guild.id] = voice_client
            
            embed = discord.Embed(
                title="✅ Joined Voice Channel",
                description=f"Joined **{voice_channel.name}**",
                color=COLORS["SUCCESS"]
            )
            await ctx.send(embed=embed)
            
        except discord.ClientException:
            embed = discord.Embed(
                title="❌ Error",
                description="I'm already connected to a voice channel!",
                color=COLORS["ERROR"]
            )
            await ctx.send(embed=embed)
    
    @commands.command(name="leave")
    async def leave_command(self, ctx):
        """Leave the voice channel"""
        voice_client = self.get_voice_client(ctx.guild.id)
        
        if not voice_client:
            embed = discord.Embed(
                title="ℹ️ Info",
                description="I'm not in a voice channel!",
                color=COLORS["INFO"]
            )
            await ctx.send(embed=embed)
            return
        
        # Clear queue and now playing
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        self.now_playing[ctx.guild.id] = None
        
        # Disconnect
        await voice_client.disconnect()
        del self.voice_clients[ctx.guild.id]
        
        embed = discord.Embed(
            title="👋 Left Voice Channel",
            color=COLORS["SUCCESS"]
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Clean up if bot is alone in voice channel"""
        if member.bot:
            return
        
        voice_client = self.get_voice_client(member.guild.id)
        if voice_client and voice_client.is_connected():
            # Check if bot is alone in voice channel (excluding itself)
            if len(voice_client.channel.members) == 1:
                # Clear queue
                queue = self.get_queue(member.guild.id)
                queue.clear()
                self.now_playing[member.guild.id] = None
                
                # Leave after 60 seconds if still alone
                await asyncio.sleep(60)
                
                if (voice_client and voice_client.is_connected() and 
                    len(voice_client.channel.members) == 1):
                    await voice_client.disconnect()
                    del self.voice_clients[member.guild.id]

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
