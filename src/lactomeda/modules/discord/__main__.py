import asyncio
from collections import deque
from lactomeda.config.constants import Language, MusicProvider, MusicURL, SpecialNames
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord.plugins.Listener import Listener 
from lactomeda.modules.discord.views.music import MusicView
from lactomeda.modules.discord.plugins.Downloader import Downloader
import discord, torch, whisper, os
from lactomeda.config.lactomeda_config import LactomedaConfig
from utils.random_int import random_int


class LactomedaDiscord(LactomedaModule):
    
    FFMPEG_OPTIONS = {  
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
        }
    
    
    def __init__(self):
        self.lactomeda_setup = LactomedaConfig.get_instance()
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.voice_states = True
        self.bot = discord.Bot(intents=self.intents)
        
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        # print(f"Using {device} device")
        # self.model = whisper.load_model("small").to(device)
        
        self.downloader = Downloader()
        self.music_provider = MusicProvider() 
        
        self.embed = None
        self.voice_channel = {}
    
    async def join_voice(self, interaction: discord.Interaction):
        server_configuration = self.lactomeda_setup.get_server_config(interaction.guild.id)
        if interaction.user.voice is None:
            await interaction.channel.send("No estas en un canal de voz")
            return
            
        if interaction.guild.voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()
            
            self.lactomeda_setup.update_server_config(interaction.guild.id, "voice_channel", voice_client) 
            # self.voice_channel[voice_client.guild.id] = voice_client
            self._log_message("Conectado a un canal de voz")
            
            # try:
            #     asyncio.create_task(self.listener_handler(voice_client))
            # except Exception as e:
            #     self._error_message(e)
            # return voice_client
    
    # async def listener_handler(self, voice_client):
    #     sink = discord.sinks.MP3Sink()
        
    #     def finished_callback(sink, *args):
    #         print("Finalizado")
            
    #     while voice_client.is_connected():
    #         print("Iniciando escucha")
    #         voice_client.start_recording(sink, finished_callback)
    #         print("Iniciando sleep") 
    #         await asyncio.sleep(5)
            
    #         print("Parando escucha")
    #         voice_client.stop_recording()
            
    #         await asyncio.sleep(2)
            
    #         audio_bytes = sink.get_all_audio()
            
    #         if not audio_bytes:
    #             print(f"No hay audio  {audio_bytes}")	
    #             continue
            
    #         # print("Escuchando", audio_bytes[0].getvalue())
    #         with open("temp_audio.mp3", "wb") as f:
    #             f.write(audio_bytes[0].getvalue())
    #             print("Archivo abierto")
                
    #         if os.stat("temp_audio.mp3").st_size == 0:
    #             print("Archivo vacio")
    #             continue
            
    #         result = self.model.transcribe("temp_audio.mp3",language=Language.ES)
    #         text = result["text"].strip()
    #         if text:
    #             print(f"Escuché: {text}")
    #             if "hola" in text.lower():
    #                 print("Hola!, te escucho correctamente")
                    
    #         sink.audio_data.clear()
                        
    
    async def play_next(self, guild_id, view: MusicView):
        server_configuration = self.lactomeda_setup.get_server_config(guild_id)
     
        if not server_configuration["queue_songs"] or len(server_configuration["queue_songs"]) == 0:
            self._log_message("No hay cola de canciones")
            return
        
        if server_configuration["current_index"] == len(server_configuration["queue_songs"]) :
            await view.create_embeds(is_last_song=True)
            self._log_message("Ya no hay canciones")           
            return  
   
        if server_configuration["is_shuffle"]:
            try:
                if len(server_configuration["index_shuffle"]) == len(server_configuration["queue_songs"]):
                    await view.create_embeds(is_last_song=True)
                    self._log_message("Ya no hay canciones")           
                    return
                
                server_configuration["current_index"] = random_int(0, len(server_configuration["queue_songs"]) - 1, server_configuration["index_shuffle"])
                print(server_configuration["current_index"])
                server_configuration["index_shuffle"].append(server_configuration["current_index"])
                song = server_configuration["queue_songs"][server_configuration["current_index"]]
                self._log_message(f"Reproduciendo {song["title"]}")
                
                await view.create_embeds(song)
                self.embed = await view.update_message()
                player = discord.FFmpegPCMAudio(song["song"], **self.FFMPEG_OPTIONS)
                voice_client = server_configuration.get("voice_channel")
                voice_client.play(player, after=lambda e: self.safe_play_next(guild_id,view, server_configuration))
            except Exception as e:
                self._error_message(e)
        else:
            try:
                song = server_configuration["queue_songs"][server_configuration["current_index"]]
                self._log_message(f"Reproduciendo {song["title"]}")
                
                await view.create_embeds(song)
                self.embed = await view.update_message()
                player = discord.FFmpegPCMAudio(song["song"], **self.FFMPEG_OPTIONS)
                voice_client = server_configuration.get("voice_channel")
                voice_client.play(player, after=lambda e: self.safe_play_next(guild_id,view, server_configuration))
            except Exception as e:
                self._error_message(e)
        
    def safe_play_next(self, guild_id,view: MusicView, server_configuration):
        if not server_configuration["is_shuffle"]:
            server_configuration["current_index"] += 1
        if server_configuration["is_stopped"]:
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
            guild_id = interaction.guild.id
            server_configuration = self.lactomeda_setup.get_server_config(guild_id)
            songs = []
            titles = []
            spotify_songs = []
            playlist = None
            is_spotify_playlist = False
            server_configuration["is_stopped"] = False
        
            await self.join_voice(interaction)
            voice_client = server_configuration.get("voice_channel")

            # if guild_id not in self.queue_songs:
            #     self.queue_songs[guild_id] = deque()
                
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
            
            
            server_configuration["queue_songs"].append(
                {"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url}
            )
            
            #pendiente reemplazar la queue con el que haya en el server_config
            # asegurarse de que todo funcione como antes
            if not voice_client.is_playing():
                
                view = MusicView(self.bot , server_configuration)
                await view.send_initial_message(interaction)
                task = asyncio.create_task(self.play_next(guild_id, view))
                # task.add_done_callback(lambda t: self._log_message("En espera de música"))
            if is_spotify_playlist:
                for song in spotify_songs:
                    song, title,artist, duration, img_url = await asyncio.create_task(self.downloader.yt_download(song))
                    server_configuration["queue_songs"].append(
                        {"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url}
                        )
                
                self._log_message(f"Playlist Agregada")
                await interaction.followup.send("Playlist Agregada",ephemeral=True)
            
            if playlist:
                songs, titles, artists, durations, imgs_urls = await self.downloader.yt_download(playlist, is_playlist=True)
                
                for i,song in enumerate(songs):
                    server_configuration["queue_songs"].append({"title":titles[i], "song":song, "artist":artists[i], "duration":durations[i], "img_url":imgs_urls[i]})

                self._log_message(f"Musica Agregada: {title}")
                await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
            
            elif not playlist and not is_spotify_playlist:
                self._log_message(f"Musica Agregada: {title}")
                await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
            

                
 
        
        @self.bot.slash_command(name="debug")
        async def debug(interaction: discord.Interaction):
            try:
                await self.join_voice(interaction)
                # await interaction.response.defer()
                # self._log_message(f"Index: {self.current_index[0]}")
                server_configuration = self.lactomeda_setup.get_server_config(interaction.guild.id)
                print(server_configuration)
                # self._log_message([song['title'] for song in server_configuration["queue_songs"]])    
                # # self._log_message(asyncio.all_tasks()) 
                # await interaction.followup.send([song['title'] for song in self.queue_songs[interaction.guild.id]])
            except Exception as e:
                self._error_message(e)
        
        self.bot.run(self.lactomeda_setup.discord_token)
        