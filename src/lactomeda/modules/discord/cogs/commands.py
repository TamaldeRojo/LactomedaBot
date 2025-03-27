import asyncio

import discord
from lactomeda.config.lactomeda_config import LactomedaConfig
from lactomeda.modules.discord.plugins.Downloader import Downloader
from lactomeda.config.constants import MusicProvider
from lactomeda.modules.discord.views.music import MusicView
from lactomeda.config import fake_interaction
from utils.random_int import random_int
from utils.url_analyzer import analyze_url


downloader = Downloader()
lactomeda_setup = LactomedaConfig.get_instance()
FFMPEG_OPTIONS = {  
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
    }

async def play_next(guild_id, view: MusicView, embed = None):
    server_configuration = lactomeda_setup.get_server_config(guild_id)
    if not server_configuration["queue_songs"] or len(server_configuration["queue_songs"]) == 0:
        print("No hay cola de canciones")
        return

    if server_configuration["current_index"] == len(server_configuration["queue_songs"]) :
        await view.create_embeds(is_last_song=True)
        print("Ya no hay canciones")           
        return  

    try:
        if server_configuration["is_shuffle"]:
            if len(server_configuration["index_shuffle"]) == len(server_configuration["queue_songs"]):
                await view.create_embeds(is_last_song=True)
                print("Ya no hay canciones")           
                return
            if not server_configuration["is_back_skip"]:
                server_configuration["current_index"] = random_int(0, len(server_configuration["queue_songs"]) - 1, server_configuration["index_shuffle"])
            else:
                server_configuration["is_back_skip"] = False

            server_configuration["index_shuffle"].append(server_configuration["current_index"])
        
        
        song = server_configuration["queue_songs"][server_configuration["current_index"]]
        await _play_song(song, server_configuration,view,guild_id)
    except Exception as e:
        print(e)


async def _play_song(song,server_configuration,view,guild_id):
    print(f"Reproduciendo {song["title"]}")
    await view.create_embeds(song)
    await view.update_message()
    player = discord.FFmpegPCMAudio(song["song"], **FFMPEG_OPTIONS)
    voice_client = server_configuration.get("voice_channel")
    
    loop = asyncio.get_event_loop()
    def after_play(error):
        if error:
            print(f"Error occurred in after_play: {error}")
        if not server_configuration["is_shuffle"]:
            server_configuration["current_index"] += 1
        if server_configuration["is_stopped"]:
            return
        
        try:
            print("calling play_next")
            coro = play_next(guild_id, view)
            asyncio.run_coroutine_threadsafe(coro, loop)
        except Exception as e:
            print(f"Error occurred in after_play: {e}")
    
    voice_client.play(player, after=after_play)
    

async def play_command(interaction, bot, query):
    # print(interaction.__dict__)
    guild_id = interaction.guild.id
    server_configuration = lactomeda_setup.get_server_config(guild_id)
    music_channel_id = server_configuration.get("default_music_channel")
    default_music_channel: discord.TextChannel = bot.get_channel(music_channel_id) if bot.get_channel(music_channel_id) else bot.get_channel(interaction.channel.id)
    
    
    songs = []
    titles = []
    spotify_songs = []
    playlist = None
    is_spotify_playlist = False
    server_configuration["is_stopped"] = False

    voice_client = server_configuration.get("voice_channel")
    
    if isinstance(interaction, discord.Interaction):
        await interaction.response.defer()
    elif isinstance(interaction, fake_interaction.FakeInteraction):
        await interaction.response.send("⏳ Dame un momento que busque tu musica...", delete_after=5)
        
    music_provider = await analyze_url(query)

    
    match music_provider:
        case MusicProvider.YOUTUBE:
            song, title, artist, duration, img_url = await downloader.yt_download(query)
        
        case MusicProvider.YOUTUBE_PLAYLIST:
            playlist = query
            query = query.split("&")[0]
            song, title, artist, duration, img_url = await downloader.yt_download(query)

        case MusicProvider.SPOTIFY:
            song_name = downloader.get_spotify_song_name(query)
            song, title,artist, duration, img_url = await downloader.yt_download(song_name)
        
        case MusicProvider.SPOTIFY_ALBUM:
            is_spotify_playlist = True
            results = await downloader.get_spotify_tracks_from_album(query)
            for track in results['items']:
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                spotify_songs.append(f"{track_name} - {artist_name}")
                
            song_name = spotify_songs.pop(0)
            song, title, artist, duration, img_url = await downloader.yt_download(song_name)
        
        case MusicProvider.SPOTIFY_PLAYLIST:
            is_spotify_playlist = True
            results = await downloader.get_spotify_names_from_playlist(query)
            for item in results['items']:
                track = item['track']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                spotify_songs.append(f"{track_name} - {artist_name}")
            song_name = spotify_songs.pop(0)
            song, title,artist, duration, img_url = await downloader.yt_download(song_name)
        
        case None:
            song, title, artist, duration, img_url  = await downloader.yt_download(query)
    
    
    server_configuration["queue_songs"].append(
        {"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url}
    )

    if not voice_client.is_playing():
        
        view = MusicView(bot , server_configuration, interaction.channel.id)
        await view.send_initial_message(interaction)
        asyncio.create_task(play_next(guild_id, view))
        # task.add_done_callback(lambda t: self._log_message("En espera de música"))
    if is_spotify_playlist:
        for song in spotify_songs:
            song, title,artist, duration, img_url = await asyncio.create_task(downloader.yt_download(song))
            server_configuration["queue_songs"].append(
                {"title":title, "song":song, "artist":artist, "duration":duration, "img_url":img_url}
                )
        
        print("Playlist Agregada")
        try:
            await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
        except (discord.HTTPException, discord.NotFound) as e:
            print(f"Error enviando mensaje de seguimiento: {e}")
            await default_music_channel.send(f"Musica Agregada: {title}",delete_after=5)
    
    if playlist:
        songs, titles, artists, durations, imgs_urls = await downloader.yt_download(playlist, is_playlist=True)
        
        for i,song in enumerate(songs):
            server_configuration["queue_songs"].append({"title":titles[i], "song":song, "artist":artists[i], "duration":durations[i], "img_url":imgs_urls[i]})

        print(f"Musica Agregada: {title}")
        try:
            await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
        except (discord.HTTPException, discord.NotFound) as e:
            print(f"Error enviando mensaje de seguimiento: {e}")
            await default_music_channel.send(f"Musica Agregada: {title}",delete_after=5)
    
    elif not playlist and not is_spotify_playlist:
         
        try:
            print(f"Musica Agregada: {title}")
            await interaction.followup.send(f"Musica Agregada: {title}",ephemeral=True)
        except (discord.HTTPException, discord.NotFound) as e:
            print(f"Error enviando mensaje de seguimiento: {e}")
            await default_music_channel.send(f"Musica Agregada: {title}",delete_after=5)
            
async def debug(self, ctx):
    pass