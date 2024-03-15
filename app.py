# import bot, os, asyncio
import discord
from decouple import config

def main():
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
        if message.author.name in ["zeropatos","zer0woo"]:
                print("[+] She is pretty as f")
                await message.add_reaction("❤️")
        if message.content.startswith('>l'):
            await message.channel.send(f'Fk mamon el {message.author.name}')
            
    
    client.run(config('tk'))


if __name__ == "__main__":
    main()


