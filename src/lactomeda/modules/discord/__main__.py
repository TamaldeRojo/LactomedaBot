import asyncio
import re
import discord 
from discord.ext import commands
from discord import app_commands
import torch 
import whisper
import os
from lactomeda.config import constants
from lactomeda.config.constants import SpecialNames
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord.cogs.commands import play_command
from lactomeda.modules.discord.cogs.messages import lactomeda_response
from lactomeda.modules.discord.plugins.ai_client import AIClient
from lactomeda.config.lactomeda_config import LactomedaConfig
from lactomeda.config.fake_interaction import FakeInteraction


class LactomedaDiscord(LactomedaModule):
    
   
    
    def __init__(self):
        self.lactomeda_setup = LactomedaConfig.get_instance()
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.voice_states = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        
        self.lactomeda_setup.bot_loop = None
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using {device} device")
        self.model = whisper.load_model("small").to(device)
        
        self.ai_client = AIClient()
        
    
    async def join_voice(self, interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.channel.send("No estas en un canal de voz")
            return
            
        if interaction.guild.voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()
            
            self.lactomeda_setup.update_server_config(interaction.guild.id, "voice_channel", voice_client) 
            self._log_message("Conectado a un canal de voz")
            
  
   
    
    def run(self):
        
        @self.bot.event
        async def on_ready():
            self._log_message(f"Logged in as {self.bot.user}")
            await self.bot.tree.sync()
            for guild in self.bot.guilds:
                self._log_message(f"Inizializando la configuración de la guild: {guild.name}: {guild.id}")
                self.lactomeda_setup.get_server_config(guild.id)
                self.ai_client.initialize(guild.id)
            
        
        @self.bot.event
        async def on_message(message):
            if message.guild is None:
                return
            server_configuration = self.lactomeda_setup.get_server_config(message.guild.id)
            conversation_history = server_configuration["conversation_history"]
            if message.author.bot:
                conversation_history.append({message.author.name : message.content})                
                return            
            conversation_history.append({message.author.name : message.content}) 
            
            if len(conversation_history) > 20:
                conversation_history.popleft()
            
            if message.reference:
                replied_msg = await message.channel.fetch_message(message.reference.message_id)
            else:
                replied_msg = message
                
                    
            
            if message.author.name in [SpecialNames.BELOVED,SpecialNames.BELOVED_2ND]:
                    await message.add_reaction("❤️")
            
            
            
            if re.search(r'\blactomeda\b', message.content, re.IGNORECASE) or replied_msg.author.id == self.bot.user.id:
                lactomeda_res, command_name, command_args = lactomeda_response(self.ai_client, message,conversation_history)
                await message.reply(lactomeda_res)  

                if command_name is None:
                    print("No detectó el comando, tal vez no haya")
                    return
                elif command_name == constants.DiscordCommands.LACTOMEDA_ORDERS["/play"]:
                    fake_interaction = FakeInteraction(self.bot, message)
                    await self.join_voice(fake_interaction)
                    if command_args: 
                        for arg in command_args:
                            query = arg
                            await play_command(fake_interaction, self.bot, query)
                            
                    else: 
                        query = "creed Higher"
                        await play_command(fake_interaction, self.bot, query)
                elif command_name == constants.DiscordCommands.LACTOMEDA_ORDERS["/debug"]:
                    pass
                elif command_name == constants.DiscordCommands.LACTOMEDA_ORDERS["join"]:
                    fake_interaction = FakeInteraction(self.bot, message)
                    # await interaction.response.defer()
                    await self.join_voice(fake_interaction)
                    
        
        @self.bot.tree.command(name="play", description="URL de la musica")
        async def play(interaction: discord.Interaction, query: str):
            await self.join_voice(interaction)

            await play_command(interaction, self.bot, query)
            

        @self.bot.tree.command(name="debug")
        async def debug(interaction: discord.Interaction):
            try:
                await self.join_voice(interaction)
                # await interaction.response.defer()
                # self._log_message(f"Index: {self.current_index[0]}")
                server_configuration = self.lactomeda_setup.get_server_config(interaction.guild.id)
                print(server_configuration)
                # print(server_configuration["conversation_history"])
                # self._log_message([song['title'] for song in server_configuration["queue_songs"]])    
                # # self._log_message(asyncio.all_tasks()) 
                # await interaction.followup.send([song['title'] for song in self.queue_songs[interaction.guild.id]])
            except Exception as e:
                self._error_message(e)
        
        self.bot.run(self.lactomeda_setup.discord_token)
        