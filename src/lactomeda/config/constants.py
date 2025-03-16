
# CONSTANTS


class Config:
    pass

class MusicProvider:
    SPOTIFY = "spotify"
    SPOTIFY_ALBUM = "spotify_album"
    SPOTIFY_PLAYLIST = "spotify_playlist"
    
    YOUTUBE = "youtube"
    YOUTUBE_PLAYLIST = "list"
    DEEZER = "deezer"
    
    
class MusicURL:
    SPOTIFY_PLAYLIST = "https://open.spotify.com/playlist/"
    SPOTIFY_ALBUM = "https://open.spotify.com/album/"
    
    
class SpecialNames:
    BELOVED = "zeropatos"
    BELOVED_2ND = "zer0woo"
    

class Denials:
    QUERY_DENIALS = ["playlist", "playlists", "list", "lists", "album", "albums", "full album", "tracks"]