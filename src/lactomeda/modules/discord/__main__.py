import asyncio
from collections import deque
from lactomeda.config.constants import MusicProvider
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord.modals.music import MusicView
from lactomeda.modules.discord.plugins.Downloader import Downloader
from . import DISCORD_TOKEN
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

GUILD_ID = 990342596717080596


class LactomedaDiscord(LactomedaModule):
    
    FFMPEG = {  
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }
    
    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.client = discord.Client(intents=self.intents)
        self.tree = app_commands.CommandTree(self.client)
        
        self.downloader = Downloader()
        self.music_provider = MusicProvider() 
        
        self.voice_channel = {}
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
            if self.queue_songs[guild_id]:
                song = self.queue_songs[guild_id].popleft()
            else:
                self._log_message("No hay más canciones en la cola")
                return
            self._log_message(f"Reproduciendo {song["title"]}")
            self._log_message(f"Siguientes: \n {self.queue_songs[guild_id]}")
            player = discord.FFmpegPCMAudio(song["song"], **self.FFMPEG)
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
        
    async def analyze_url(self, url):
        splited_url = url.split(".")
        if self.music_provider.YOUTUBE in splited_url:
            return self.music_provider.YOUTUBE
        elif self.music_provider.SPOTIFY in splited_url:
            return self.music_provider.SPOTIFY
        else:
            return None
            
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
                spotify_songs = []
                is_spotify_playlist = False
                        
                guild_id = interaction.guild.id
                voice_client = await self.join_voice(interaction)
                voice_client = self.voice_channel[guild_id]
                
                if guild_id not in self.queue_songs:
                    self.queue_songs[guild_id] = deque()
                    
                await interaction.response.defer()
                
                music_provider = await self.analyze_url(query)
                
                match music_provider:
                    case self.music_provider.YOUTUBE:
                        song, title, playlist = await self.downloader.yt_download(query)

                    case self.music_provider.SPOTIFY:
                        
                        if query.startswith("https://open.spotify.com/playlist/") or query.startswith("https://open.spotify.com/album/"):
                            is_spotify_playlist = True
                            results = await self.downloader.get_spotify_names_from_playlist(query)
                            for item in results['items']:
                                track = item['track']
                                track_name = track['name']
                                artist_name = track['artists'][0]['name']
                                spotify_songs.append(f"{track_name} - {artist_name}")
                    
                            song_name = spotify_songs.pop(0)
                        else: 
                        
                            song_name = self.downloader.get_spotify_song_name(query)
                            
                        print(song_name)
                        song, title, playlist = await self.downloader.yt_download(song_name, is_name=True)
                    
                    case None:
                        song, title, playlist = await self.downloader.yt_download(query, is_name=True)
                    
                self.queue_songs[guild_id].append({"title":title, "song":song})
                if not voice_client.is_playing():
                    
                    await self.play_next(guild_id)
                    view = MusicView(self.client , self.queue_songs[guild_id])
                    await interaction.followup.send("Música reproducida", view=view)
                    
                    if is_spotify_playlist:
                        for song in spotify_songs:
                            song, title, playlist = await self.downloader.yt_download(song, is_name=True)
                            self.queue_songs[guild_id].append({"title":title, "song":song})
                    elif playlist:
                        songs, titles = await self.downloader.yt_download(playlist, is_playlist=True)
                        
                        for i,song in enumerate(songs):
                            self.queue_songs[guild_id].append({"title":titles[i], "song":song})
                            
                    # print(any(song["title"] == title for song in self.queue_songs[guild_id]))
                else:
                    await interaction.channel.send("Ya estas reproduciendo una musica")
                            
            except Exception as e:
                self._error_message(e)
        
        
     
        
        self.client.run(DISCORD_TOKEN)
        