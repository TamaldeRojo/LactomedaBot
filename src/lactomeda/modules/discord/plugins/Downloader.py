import asyncio, discord, yt_dlp, spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
    
    def get_spotify_song_name(self, url):
        track_info = self.sp.track(url)
        song_name = track_info.get("name","Unkown song")
        artist_name = track_info['artists'][0]["name"]
        return f"{song_name} - {artist_name}"

    async def get_spotify_names_from_playlist(self, url):
        #https://open.spotify.com/playlist/6pER44X99fa5VbqIkagRgv?si=lFZQd_zcRkWMQSQ9aZPB_A
        playlist_id = url.split("playlist/")[1].split("?")[0] if len(url.split("playlist/")) > 1 else url.split("album/")[1].split("?")[0]
        results = self.sp.playlist_tracks(playlist_id)
        return results
        
    async def run(self):
        pass 
    
    async def yt_download(self,query, is_playlist=False, is_name=False):
        
        with yt_dlp.YoutubeDL(self.yt_dlp_options) as ytdl:
              
            
            if is_playlist:
                  
                playlist_data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))
                songs = [entry["url"] for entry in playlist_data["entries"][1:]] 
                titles = [entry["title"] for entry in playlist_data["entries"][1:]]
                
                return [songs,titles]
              
            else:  
                playlist = None
                        
                if len(query.split("&")) > 1:
                    playlist = query
                    query = query.split("&")[0]
                    
                    
                data = await asyncio.to_thread(lambda: ytdl.extract_info(query, download=False))   
                if is_name:
                    if 'entries' in data:
                        return data['entries'][0]['url'], data['entries'][0]['title'], playlist
                if playlist:
                    self._log_message("Playlist encontrada")

                self._log_message("Cancion encontrada")  
                song = data["url"]
                title = data["title"]
                
                return song, title, playlist
