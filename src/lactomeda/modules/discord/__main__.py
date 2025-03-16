import asyncio
from collections import deque
from lactomeda.config.constants import MusicProvider, MusicURL, SpecialNames
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord.views.music import MusicView
from lactomeda.modules.discord.plugins.Downloader import Downloader
from . import DISCORD_TOKEN
import discord



class LactomedaDiscord(LactomedaModule):
    
    FFMPEG_OPTIONS = {  
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }
    
    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = discord.Bot(intents=self.intents)
        
        self.downloader = Downloader()
        self.music_provider = MusicProvider() 
        
        self.embed = None
        self.voice_channel = {}
        self.queue_songs = {} #Canciones que se van a reproducir
        self.current_index = [0] # se tiene que resetear cuando se detenga el bot o salga
        self.is_stopped = [False] #Boton detener musica, es una lista para que sea inmutable xd
    
    async def join_voice(self, interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.channel.send("No estas en un canal de voz")
            return
            
        if interaction.guild.voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()
            self.voice_channel[voice_client.guild.id] = voice_client
            self._log_message("Conectado a un canal de voz")
            return voice_client
        
    async def play_next(self, guild_id, view: MusicView):
        print(self.current_index[0])
        if not self.queue_songs[guild_id] or len(self.queue_songs[guild_id]) == 0:
            self._log_message("No hay cola de canciones")
        
        if self.current_index[0] == len(self.queue_songs[guild_id]) :
            await view.create_embeds(is_last_song=True)
            self._log_message("Ya no hay canciones")           
            return     
        
        try:
            song = self.queue_songs[guild_id][self.current_index[0]]
            self._log_message(f"Reproduciendo {song["title"]}")
            
            await view.create_embeds(song)
            self.embed = await view.update_message()
            player = discord.FFmpegPCMAudio(song["song"], **self.FFMPEG_OPTIONS)
            voice_client = self.voice_channel[guild_id]
            voice_client.play(player, after=lambda e: self.safe_play_next(guild_id,view))
        except Exception as e:
            self._error_message(e)
        
    def safe_play_next(self, guild_id,view: MusicView):
        self.current_index[0] += 1 
        if self.is_stopped[0]:
            return
        loop = self.bot.loop  

        if loop.is_closed():
            self._error_message("Event loop is closed. Cannot schedule play_next.")
            return

        future = asyncio.run_coroutine_threadsafe(self.play_next(guild_id, view), loop)
        try:
            future.result()
        except Exception as e:
            self._error_message(e)
        
    async def analyze_url(self, url):
        splited_url = url.split(".")
        if self.music_provider.YOUTUBE in splited_url:
            if len(splited_url[2].split("&")) > 1:
                return self.music_provider.YOUTUBE_PLAYLIST
            return self.music_provider.YOUTUBE
        elif self.music_provider.SPOTIFY in splited_url:
            if splited_url[2].split("/")[1].startswith("playlist"):
                return self.music_provider.SPOTIFY_PLAYLIST
            elif splited_url[2].split("/")[1].startswith("album"):
                return self.music_provider.SPOTIFY_ALBUM
            return self.music_provider.SPOTIFY
        else:
            return None
            
    def run(self):
        
        @self.bot.event
        async def on_ready():
            self._log_message(f"Logged in as {self.bot.user}")
        
        @self.bot.event
        async def on_message(message):
            if message.author.bot:
                return
            
            if message.author.name in [SpecialNames.BELOVED,SpecialNames.BELOVED_2ND]:
                    await message.add_reaction("❤️")
            

            
        
        @self.bot.slash_command(name="play")
        async def play(interaction: discord.Interaction, query: str):
            """URL de la musica"""
            try:
                songs = []
                titles = []
                spotify_songs = []
                playlist = None
                is_spotify_playlist = False
                
                self.is_stopped[0] = False
     
                guild_id = interaction.guild.id
                voice_client = await self.join_voice(interaction)
                voice_client = self.voice_channel[guild_id]
 
                if guild_id not in self.queue_songs:
                    self.queue_songs[guild_id] = deque()
                    
                await interaction.response.defer()
                
                music_provider = await self.analyze_url(query)
                
                match music_provider:
                    case self.music_provider.YOUTUBE:
                        song, title, artist, duration, img_url = await self.downloader.yt_download(query)
                    
                    case self.music_provider.YOUTUBE_PLAYLIST:
                        playlist = query
                        query = query.split("&")[0]
                        song, title, artist, duration, img_url = await self.downloader.yt_download(query)

                    case self.music_provider.SPOTIFY:
                        song_name = self.downloader.get_spotify_song_name(query)
                        song, title,artist, duration, img_url = await self.downloader.yt_download(song_name)
                    
                    case self.music_provider.SPOTIFY_ALBUM:
                        is_spotify_playlist = True
                        results = await self.downloader.get_spotify_tracks_from_album(query)
                        for track in results['items']:
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            spotify_songs.append(f"{track_name} - {artist_name}")
                            
                        song_name = spotify_songs.pop(0)
                        song, title, artist, duration, img_url = await self.downloader.yt_download(song_name)
                    
                    case self.music_provider.SPOTIFY_PLAYLIST:
                        is_spotify_playlist = True
                        results = await self.downloader.get_spotify_names_from_playlist(query)
                        for item in results['items']:
                            track = item['track']
                            track_name = track['name']
                            artist_name = track['artists'][0]['name']
                            spotify_songs.append(f"{track_name} - {artist_name}")
                        song_name = spotify_songs.pop(0)
                        song, title,artist, duration, img_url = await self.downloader.yt_download(song_name)
                    
                    case None:
                        song, title, artist, duration, img_url  = await self.downloader.yt_download(query)
                
                
                self.queue_songs[guild_id].append({"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url})
                            
                if not voice_client.is_playing():
                    
                    view = MusicView(self.bot , self.queue_songs[guild_id],self.current_index, self.is_stopped)
                    await view.send_initial_message(interaction)
                    task = asyncio.create_task(self.play_next(guild_id, view))
                    # task.add_done_callback(lambda t: self._log_message("En espera de música"))
                if is_spotify_playlist:
                    for song in spotify_songs:
                        song, title,artist, duration, img_url = await asyncio.create_task(self.downloader.yt_download(song))
                        self.queue_songs[guild_id].append({"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url})
                    
                    self._log_message(f"Playlist Agregada")
                    await interaction.followup.send("Playlist Agregada",ephemeral=True)
                
                if playlist:
                    songs, titles, artists, durations, imgs_urls = await self.downloader.yt_download(playlist, is_playlist=True)
                    
                    for i,song in enumerate(songs):
                        self.queue_songs[guild_id].append({"title":titles[i], "song":song, "artist":artists[i], "duration":durations[i], "img_url":imgs_urls[i]})

                    self._log_message(f"Musica Agregada: {title}")
                    await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
                
                elif not playlist and not is_spotify_playlist:
                    self._log_message(f"Musica Agregada: {title}")
                    await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
                
                        
            except Exception as e:
                self._error_message(e)
                
 
        
        @self.bot.slash_command(name="debug")
        async def debug(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                self._log_message(f"Index: {self.current_index[0]}")
                self._log_message([song['title'] for song in self.queue_songs[interaction.guild.id]])    
                # self._log_message(asyncio.all_tasks()) 
                await interaction.followup.send([song['title'] for song in self.queue_songs[interaction.guild.id]])
            except Exception as e:
                self._error_message(e)
        
        self.bot.run(DISCORD_TOKEN)
        