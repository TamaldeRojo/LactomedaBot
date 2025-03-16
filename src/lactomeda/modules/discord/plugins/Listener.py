from lactomeda.modules.base import LactomedaModule
import asyncio, io, discord, openai

class Listener():
    
    def __init__(self):
        self.buffer_audio = io.BytesIO()
    
    def write(self, data):
        self.buffer_audio.write(data)
    
    def get_audio(self):
        return self.buffer_audio.getvalue() #returns the audio data as bytes
