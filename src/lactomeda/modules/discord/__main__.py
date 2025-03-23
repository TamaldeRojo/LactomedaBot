import asyncio
from collections import deque
import json
import re
from lactomeda.config import constants
from lactomeda.config.constants import Language, MusicProvider, MusicURL, SpecialNames
from lactomeda.modules.base import LactomedaModule
from lactomeda.modules.discord.cogs.commands import play_command
from lactomeda.modules.discord.cogs.messages import lactomeda_response
from lactomeda.modules.discord.plugins.Listener import Listener 
from lactomeda.modules.discord.plugins.ai_client import AIClient
from lactomeda.modules.discord.views.music import MusicView
import discord, torch, whisper, os
from lactomeda.config.lactomeda_config import LactomedaConfig
from utils.fake_interaction import FakeInteraction
from utils.random_int import random_int


class LactomedaDiscord(LactomedaModule):
    
   
    
    def __init__(self):
        self.lactomeda_setup = LactomedaConfig.get_instance()
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.voice_states = True
        self.bot = discord.Bot(intents=self.intents)
        self.lactomeda_setup.bot_loop = self.bot.loop
        
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        # print(f"Using {device} device")
        # self.model = whisper.load_model("small").to(device)
        
        self.ai_client = AIClient()
        self.voice_channel = {}
        
    
    async def join_voice(self, interaction: discord.Interaction):
        server_configuration = self.lactomeda_setup.get_server_config(interaction.guild.id)
        if interaction.user.voice is None:
            await interaction.channel.send("No estas en un canal de voz")
            return
            
        if interaction.guild.voice_client is None:
            voice_client = await interaction.user.voice.channel.connect()
            
            self.lactomeda_setup.update_server_config(interaction.guild.id, "voice_channel", voice_client) 
            # self.voice_channel[voice_client.guild.id] = voice_client
            self._log_message("Conectado a un canal de voz")
            
            # try:
            #     asyncio.create_task(self.listener_handler(voice_client))
            # except Exception as e:
            #     self._error_message(e)
            # return voice_client
    
    # async def listener_handler(self, voice_client):
    #     sink = discord.sinks.MP3Sink()
        
    #     def finished_callback(sink, *args):
    #         print("Finalizado")
            
    #     while voice_client.is_connected():
    #         print("Iniciando escucha")
    #         voice_client.start_recording(sink, finished_callback)
    #         print("Iniciando sleep") 
    #         await asyncio.sleep(5)
            
    #         print("Parando escucha")
    #         voice_client.stop_recording()
            
    #         await asyncio.sleep(2)
            
    #         audio_bytes = sink.get_all_audio()
            
    #         if not audio_bytes:
    #             print(f"No hay audio  {audio_bytes}")	
    #             continue
            
    #         # print("Escuchando", audio_bytes[0].getvalue())
    #         with open("temp_audio.mp3", "wb") as f:
    #             f.write(audio_bytes[0].getvalue())
    #             print("Archivo abierto")
                
    #         if os.stat("temp_audio.mp3").st_size == 0:
    #             print("Archivo vacio")
    #             continue
            
    #         result = self.model.transcribe("temp_audio.mp3",language=Language.ES)
    #         text = result["text"].strip()
    #         if text:
    #             print(f"Escuché: {text}")
    #             if "hola" in text.lower():
    #                 print("Hola!, te escucho correctamente")
                    
    #         sink.audio_data.clear()
                                     
    # async def execute_slash_command(self, interaction):
    #     command = self.bot.get_application_command('play')
    #     if command:
    #         await play_command(interaction, self.bot, args[0] if args else "")
    
    def run(self):
        
        @self.bot.event
        async def on_ready():
            self._log_message(f"Logged in as {self.bot.user}")
            for guild in self.bot.guilds:
                self._log_message(f"Inizializando la configuración de la guild: {guild.name}: {guild.id}")
                self.ai_client.initialize(guild.id)
            
        
        @self.bot.event
        async def on_message(message):
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

                if command_name == None:
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
                    
        
        @self.bot.slash_command(name="play")
        async def play(interaction: discord.Interaction, query: str):
            """URL de la musica"""
            await self.join_voice(interaction)

            await play_command(interaction, self.bot, query)
            

        @self.bot.slash_command(name="debug")
        async def debug(interaction: discord.Interaction):
            try:
                await self.join_voice(interaction)
                # await interaction.response.defer()
                # self._log_message(f"Index: {self.current_index[0]}")
                server_configuration = self.lactomeda_setup.get_server_config(interaction.guild.id)
                print(server_configuration)
                print(server_configuration["conversation_history"])
                # self._log_message([song['title'] for song in server_configuration["queue_songs"]])    
                # # self._log_message(asyncio.all_tasks()) 
                # await interaction.followup.send([song['title'] for song in self.queue_songs[interaction.guild.id]])
            except Exception as e:
                self._error_message(e)
        
        self.bot.run(self.lactomeda_setup.discord_token)
        