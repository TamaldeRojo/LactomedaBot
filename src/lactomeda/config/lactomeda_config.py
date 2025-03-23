from decouple import config
from collections import deque

DISCORD_TOKEN = config("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = config("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = config("SPOTIFY_CLIENT_SECRET")
OPENAI_API_KEY = config("OPENAI_API_KEY")


class LactomedaConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
            
        return cls._instance
    
    def _initialize(self):
        self.discord_token = DISCORD_TOKEN
        self.spotify_client_id = SPOTIFY_CLIENT_ID
        self.spotify_client_secret = SPOTIFY_CLIENT_SECRET
        self.openai_api_key = OPENAI_API_KEY
        self._instance.server_configs = {}
        self._instance.bot_loop = None
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def get_bot_loop(self):
        return self.bot_loop
    
    def get_server_config(self, guild_id: int):
        if guild_id not in self.server_configs:
            self.server_configs[guild_id] = self._default_server_config()
        return self.server_configs[guild_id]
    
    def update_server_config(self, guild_id: int, key: str, value):
        self.get_server_config(guild_id)[key] = value
        
    def reset_server_config(self, guild_id: int):
        self.get_server_config[guild_id] = self._default_server_config()
    
    def _default_server_config(self):
        return  {
            "language": "es",
            "queue_songs": deque(),
            "current_index": 0,
            "is_stopped": False,
            "voice_channel": {},
            "is_shuffle": False,
            "index_shuffle": deque(),
            "is_back_skip": False,
            "default_music_channel": 1352430281390555199#1071894534021189803
        }
    
    def __init__(self):
        pass
            
