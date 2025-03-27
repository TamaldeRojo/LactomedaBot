from lactomeda.config.constants import MusicProvider


async def analyze_url(url:str):
        splited_url = url.split(".")
        if MusicProvider.YOUTUBE in splited_url:
            if MusicProvider.YOUTUBE_PLAYLIST in splited_url[2].split("&"):
                return MusicProvider.YOUTUBE_PLAYLIST
            return MusicProvider.YOUTUBE
        elif MusicProvider.SPOTIFY in splited_url:
            if splited_url[2].split("/")[1].startswith("playlist"):
                return MusicProvider.SPOTIFY_PLAYLIST
            elif splited_url[2].split("/")[1].startswith("album"):
                return MusicProvider.SPOTIFY_ALBUM
            return MusicProvider.SPOTIFY
        else:
            return None