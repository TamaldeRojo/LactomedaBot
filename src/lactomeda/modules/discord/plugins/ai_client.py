import asyncio
import discord
from openai import OpenAI
from lactomeda.config.ai_response import AIResponse
from lactomeda.config.lactomeda_config import LactomedaConfig
from lactomeda.modules.base import LactomedaModule
from lactomeda.personality.personality import get_personality




class AIClient(LactomedaModule):
    def __init__(self):
        self.lactomeda_setup = LactomedaConfig.get_instance()
        self.client = OpenAI(api_key=self.lactomeda_setup.openai_api_key)
        self.model = "gpt-4o-mini-2024-07-18"
        self.lang = "en"

    def initialize(self, guild_id: int):
        self.server_configuration = self.lactomeda_setup.get_server_config(guild_id)
        self.lang = self.server_configuration["language"]
        self.lactomeda_context_prompt = get_personality(self.server_configuration)

    def send_prompt(self, prompt: str):
        return self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.lactomeda_context_prompt.strip()},
                {"role": "user", "content": prompt}
            ],
            response_format= AIResponse
        )
        
        
    def run(self):
        pass
    