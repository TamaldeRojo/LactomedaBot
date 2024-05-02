import discord, asyncio, yt_dlp
from decouple import config
from collections import deque
from discord.ext import commands


class LactomedaBot():
    def __init__(self):
        self.listSongs = []
        self.queuSongs = deque(self.listSongs)
        
    # @commands.command()
    async def joinVc(self,message,voiceClients):
        try:
            if message.author.voice is None:
                await message.channel.send("No estas en un canal de voz mocoso")
                return
            
            if message.guild.voice_client is None:
                voiceClient = await message.author.voice.channel.connect()
                voiceClients[voiceClient.guild.id] = voiceClient
                print("[+] Connected to voice channel")
                return True
                
        except Exception as e:
            print(f"[-] There was an error while joining a voice channel: {e}")
        
        
        
    async def musicYt(self,message,voiceClients,ffmpeg_options):
        try:
            yt_dlp_options = {"format" : "bestaudio"}
            # print(str(message.content).split()[1])
            jVc = await self.joinVc(message,voiceClients)
            if jVc is None:
                return
            url = message.content.split()[1]
            self.queuSongs.append(url)
            print(self.queuSongs)
            
            with yt_dlp.YoutubeDL(yt_dlp_options) as ytdl:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url,download=False))
                song = data["url"]
                voiceClient = voiceClients[message.guild.id]
                if voiceClient is not None:
                    player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
                    voiceClient.play(player, after=lambda e: print(f"[-] Player error: {e}"))
                else:
                    print("[+] Lactomeda is already playing something")
        except Exception as e:
            print(f'[-] An exception occurred: {e}')

    def runBot(self):
        voiceClients = {}
       
        
        ffmpeg_options = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options':"-vn"}
        
         # bot.runDiscordBot()
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f'We have logged in as {client.user}')
            
        @client.event
        async def on_message(message):
            if message.author == client.user:
                return
            if message.author.name in ["zeropatos","zer0woo","megustaahri"]:
                    print("[+] She is pretty as f")
                    await message.add_reaction("❤️")
            if message.content.startswith('-p ') or message.content.startswith('-P '):
               await self.musicYt(message=message,voiceClients=voiceClients,ffmpeg_options=ffmpeg_options)
        
        client.run(config('tk'))