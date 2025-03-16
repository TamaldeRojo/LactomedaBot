import asyncio, discord, yt_dlp, spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from lactomeda.config.constants import Denials
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


#https://open.spotify.com/playlist/6pER44X99fa5VbqIkagRgv?si=hNyu_yRUTQqHoATZMk3Itg

class Downloader(LactomedaModule):
    
    yt_dlp_options = {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                'quiet': True,
                'ignore_no_formats_error': True                
            }
        
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
        pass
    
    
    
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
    
    async def yt_download(self,query, is_playlist=False, is_name=False):
        
        with yt_dlp.YoutubeDL(self.yt_dlp_options) as ytdl:
              
            
            if is_playlist:
                  
                playlist_data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))
            
                songs = [entry.get("url","URL desconocido") for entry in playlist_data["entries"][1:]]
                titles = [entry.get("title","Title desconocido") for entry in playlist_data["entries"][1:]]
                artists = [entry.get("uploader","Artista desconocido") for entry in playlist_data["entries"][1:]]
                durations = [entry.get("duration",0) for entry in playlist_data["entries"][1:]]
                img_url = [entry.get("thumbnail", "") for entry in playlist_data["entries"][1:]]
            
                    
                return [songs,titles,artists,durations,img_url]
              
            else:  
                download_index = 0
                if not self.is_url(query):
                    query += " cancion"
                data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))   
                
                if bool(set(map(str.lower, data['entries'][0]['title'].split(" "))) & set(map(str.lower, Denials.QUERY_DENIALS))):
                    download_index += 1
                
                self._log_message("Cancion lista")  
                if 'entries' in data:
                    return data['entries'][download_index]['url'], data['entries'][download_index]['title'], data['entries'][download_index]['uploader'], data['entries'][download_index]['duration'], data['entries'][download_index]['thumbnail']
                else:
                    self._error_message("No se encontro ninguna musica")
                    raise NotImplementedError
