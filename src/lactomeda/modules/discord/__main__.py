import asyncio
from collections import deque
from lactomeda.modules.base import LactomedaModule
from . import DISCORD_TOKEN
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

GUILD_ID = 990342596717080596


class LactomedaDiscord(LactomedaModule):
    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
        self.tree = app_commands.CommandTree(self.client)
        self.voice_channel = {}
        self.yt_dlp_options = {
                'format': 'bestaudio/best',
                'default_search': 'auto',
                # 'playliststart': 1,
                # 'extract_flat': False,
                # 'playlistend': 50,
                'quiet': True,
                'ignore_no_formats_error': True                
            }
        
        self.ffmpeg = {  
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }
        self.queue_songs = {}
        
        
    
    async def join_voice(self, interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.channel.send("No estas en un canal de voz")
            return
            
        if interaction.guild.voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()
            self.voice_channel[voice_client.guild.id] = voice_client
            self._log_message("Conectado a un canal de voz")
            return voice_client
        
        
    async def play_next(self, guild_id):
        self._log_message(f"Reproduciendo la siguiente musica")
        if self.queue_songs[guild_id]:
            song = self.queue_songs[guild_id].popleft()
            self._log_message(f"Reproduciendo {song["title"]}")
            self._log_message(f"Siguientes: \n {self.queue_songs[guild_id]}")
            player = discord.FFmpegPCMAudio(song["song"], **self.ffmpeg)
            voice_client = self.voice_channel[guild_id]
            voice_client.play(player, after=lambda e: self.safe_play_next(guild_id))
            
    def safe_play_next(self, guild_id):
        loop = self.client.loop  
    
        if loop.is_closed():
            print("Event loop is closed. Cannot schedule play_next.")
            return

        future = asyncio.run_coroutine_threadsafe(self.play_next(guild_id), loop)
        try:
            future.result()
        except Exception as e:
            self._error_message(e)
            

            
    def run(self):
        
        @self.client.event
        async def on_ready():
            print(f"Logged in as {self.client.user}")
            await self.tree.sync()
        
        @self.client.event
        async def on_message(message):
            if message.author.bot:
                return
            
            if message.author.name in ["zeropatos","zer0woo"]:
                    await message.add_reaction("❤️")
            

            
        
        @self.tree.command(name="play", description="Reproduce musica en el canal de voz")
        @app_commands.describe(query="URL de la musica")
        async def play(interaction: discord.Interaction, query: str):
            try:
                songs = []
                titles = []
                
                guild_id = interaction.guild.id
                voice_client = await self.join_voice(interaction)
                voice_client = self.voice_channel[guild_id]
                
                if guild_id not in self.queue_songs:
                    self.queue_songs[guild_id] = deque()
                # await interaction.response.defer()
                
                #if query == word -> spotify or deezer 
                #if query == url -> check if it is from youtube, spotify or deezer etc..
                
                #if query and youtube url 
                
                with yt_dlp.YoutubeDL(self.yt_dlp_options) as ytdl:
                    playlist = None
                          
                    if len(query.split("&")) > 1:
                        playlist = query
                        query = query.split("&")[0]
                        
                        
                    data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))
                 
                    print("DEBUG 1")
                    if playlist:
                        self._log_message("Playlist encontrada")

                    # self._log_message("Cancion encontrada")                        
                    song = data["url"]
                    title = data["title"]
                    self.queue_songs[guild_id].append({"title":title, "song":song})
                
            
                    if not voice_client.is_playing():
                        await self.play_next(guild_id)
                        if playlist:
                            print("DEBUG 2")
                            playlist_data = await asyncio.to_thread(lambda: ytdl.extract_info(playlist, download=False))
                            songs = [entry["url"] for entry in playlist_data["entries"][1:]] 
                            titles = [entry["title"] for entry in playlist_data["entries"][1:]]
                            for i,song in enumerate(songs):
                                self.queue_songs[guild_id].append({"title":titles[i], "song":song})
                            print(self.queue_songs)
                    else:
                        print(self.queue_songs)
                        await interaction.channel.send("Ya estas reproduciendo una musica")
            
            except Exception as e:
                self._error_message(e)
        
        self.client.run(DISCORD_TOKEN)
        