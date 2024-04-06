import discord, os, asyncio, yt_dlp
from decouple import config
from collections import deque


class LactomedaBot():
    def __init__(self):
        self.listSongs = []
        self.queuSongs = deque(self.listSongs)
        
    async def joinToMusicYt(self,message,voiceClients,ytdl,ffmpeg_options):
        try:
            voiceClient = await message.author.voice.channel.connect()
            voiceClients[voiceClient.guild.id] = voiceClient
            
        except Exception as e:
            
            print(f"[-] There was an error of type: {e}")
        try:
            # print(str(message.content).split()[1])
            url = message.content.split()[1]
            self.queuSongs.append(url)
            print(self.queuSongs)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url,download=False))
            song = data["url"]
            print(f"[+] {data}")
            player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
            voiceClients[message.guild.id].play(player)
            # print("Muac")
        except Exception as e:
            print('An exception occurred')

    def runBot(self):
        voiceClients = {}
        yt_dlp_options = {"format" : "bestaudio/best"}
        ytdl = yt_dlp.YoutubeDL(yt_dlp_options)
        
        ffmpeg_options = {'options':"-vn"}
        
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
               await self.joinToMusicYt(message=message,voiceClients=voiceClients,ytdl=ytdl,ffmpeg_options=ffmpeg_options)
        
        client.run(config('tk'))