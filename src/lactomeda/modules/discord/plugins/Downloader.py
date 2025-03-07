import asyncio
import discord
import yt_dlp

from lactomeda.modules.base import LactomedaModule


class Downloader(LactomedaModule):
    
    yt_dlp_options = {
                'format': 'bestaudio/best',
                'default_search': 'auto',
                # 'playliststart': 1,
                # 'extract_flat': False,
                # 'playlistend': 50,
                'quiet': True,
                'ignore_no_formats_error': True                
            }
        
    
    
    def __init__(self):
        pass
    
    async def run(self):
        pass
        
   
    async def yt_download(self,query, is_playlist=False):
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
                
                if playlist:
                    self._log_message("Playlist encontrada")

                self._log_message("Cancion encontrada")                        
                song = data["url"]
                title = data["title"]
                
                return [song,title,playlist]
