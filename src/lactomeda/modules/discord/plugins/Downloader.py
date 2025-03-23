import asyncio, discord, yt_dlp, spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from lactomeda.config.constants import Denials
from lactomeda.modules.base import LactomedaModule
from lactomeda.config.lactomeda_config import LactomedaConfig

#https://open.spotify.com/playlist/6pER44X99fa5VbqIkagRgv?si=hNyu_yRUTQqHoATZMk3Itg

YTDLP_OPTIONS = {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                  "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                'quiet': True,
                'ignore_no_formats_error': True,
                'get_bypass': True,
                "lazy_playlist": True,
                                
            }
SINGLE_YTDLP_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': True, 
        'default_search': 'ytsearch',
        "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        'quiet': True,
        'outtmpl': 'songs/%(title)s.%(ext)s',
        'get_bypass': True,
        "lazy_playlist": True,

    }

class Downloader(LactomedaModule):
    
    
        
    def __init__(self):
        self.lactomeda_config = LactomedaConfig.get_instance()
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(self.lactomeda_config.spotify_client_id, self.lactomeda_config.spotify_client_secret))
        self.current_ytdlp_options = YTDLP_OPTIONS
        self._flag = False
    
    
    def is_url(self, query: str):
        patron = re.compile(r'^(https?:\/\/)?(www\.)?[\w\-]+(\.[a-z]{2,})+([\/\w\-\.\?\=\#]*)*$', re.IGNORECASE)
        return bool(patron.match(query))
        
    
    
    def get_spotify_song_name(self, url: str):
        track_info = self.sp.track(url)
        song_name = track_info.get("name","Unkown song")
        artist_name = track_info['artists'][0]["name"]
        return f"{song_name} - {artist_name}"

    async def get_spotify_names_from_playlist(self, url: str):
        playlist_id = url.split("/")[-1].split("?")[0] 
        results = self.sp.playlist_tracks(playlist_id)
        return results
    
    async def get_spotify_tracks_from_album(self, album_url: str):
        album_id = album_url.split("/")[-1].split("?")[0] 
        album_tracks = self.sp.album_tracks(album_id)
        return album_tracks 
        
    async def run(self):
        pass 
    
    async def yt_download(self,query, is_playlist=False):
        
        self.current_ytdlp_options = YTDLP_OPTIONS if is_playlist else SINGLE_YTDLP_OPTIONS
        
        with yt_dlp.YoutubeDL(self.current_ytdlp_options) as ytdl:
              
            
            if is_playlist:
                  
                playlist_data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))
            
                songs = [entry.get("url","URL desconocido") for entry in playlist_data["entries"][1:]]
                titles = [entry.get("title","Title desconocido") for entry in playlist_data["entries"][1:]]
                artists = [entry.get("uploader","Artista desconocido") for entry in playlist_data["entries"][1:]]
                durations = [entry.get("duration",0) for entry in playlist_data["entries"][1:]]
                img_url = [entry.get("thumbnail", "") for entry in playlist_data["entries"][1:]]
            
                    
                return [songs,titles,artists,durations,img_url]
              
            else:  
                data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))   
                
                if 'entries' in data:
                    entries = data['entries']    
                    valid_entries = [
                        entry for entry in entries
                        if not (set(map(str.lower, entry['title'].split())) & set(map(str.lower, Denials.QUERY_DENIALS)))
                    ]
                else:
                    valid_entries = [data]
                    # self._error_message("No se encontró ninguna música.")
       
                if not valid_entries:
                    query += " cancion"
                    self._log_message(f"intentando de nuevo con query modificado, {query}")
                    if not self._flag:
                        self._flag = True
                        return await self.yt_download(query)
                    else:
                        self._error_message("No se encontró ninguna música después de filtrar.")
                        return 
                    
                else:
                    self._log_message("Cancion lista") 
                    best_match = valid_entries[0] 
                    return best_match['url'], best_match['title'], best_match['uploader'], best_match['duration'], best_match['thumbnail']  
