
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
    QUERY_DENIALS = [
        "playlist", "playlists", "list", "lists",
        "album", "albums", "full album", "album}","album)","(album)","(fullalbum)" "fullalbum","(album"
        "tracks",
        ]
    

class AltImgs:
    EMBED_ALT_IMG = "https://i.pinimg.com/736x/62/c2/bf/62c2bfd3e4d2c91b3fb3e1414a3643fa.jpg"
    

class Language:
    ES = "es"
    EN = "en"