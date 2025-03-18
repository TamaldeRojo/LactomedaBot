from decouple import config
from collections import deque

DISCORD_TOKEN = config("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = config("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = config("SPOTIFY_CLIENT_SECRET")

class LactomedaConfig:
    _instance = None
    
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            cls.discord_token = DISCORD_TOKEN
            cls.spotify_client_id = SPOTIFY_CLIENT_ID
            cls.spotify_client_secret = SPOTIFY_CLIENT_SECRET
            
            cls._instance.server_configs = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls()
    
    def get_server_config(self, guild_id: int):
        if guild_id not in self.server_configs:
            self.server_configs[guild_id] = {
                "queue_songs": deque(),
                "current_index": 0,
                "is_stopped": False,
                "voice_channel": {},
                "is_shuffle": False,
                "index_shuffle": deque()
            }
        return self.server_configs[guild_id]
    
    def update_server_config(self, guild_id: int, key: str, value):
        server_config = self.get_server_config(guild_id)
        server_config[key] = value
        
    def reset_server_config(self, guild_id: int):
        self.server_configs[guild_id] = {
                "queue_songs": deque(),
                "current_index": 0,
                "is_stopped": False,
                "voice_channel": {},
                "is_shuffle": False,
                "index_shuffle": deque()
            }
    
    def __init__(self):
        pass
            
