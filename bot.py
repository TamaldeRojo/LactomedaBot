import responses
from discord import Intents,Client, Message
from decouple import config



async def sendMsg(msg,userMsg,isPriv):
    try:
      response = responses.handleRes(userMsg)
      await msg.author.send(response) if isPriv else await msg.channel.send(response)
    except Exception as e:
      print(f'An exception occurred: {e}')
      
      
def runDiscordBot():
    tk =  config('tk')
    
    intents: Intents = Intents.default()
    intents.message_content = True
    client: Client = Client(intents=intents)
    
    @client.event
    async def onReady() -> None:
        print(f"{client.user} is now running! ")
    
    @client.event
    async def onMsg(msg : Message) -> None:
        if msg.author == client.user:
            return
        username: str = str(msg.author)
        userMsg: str = msg.content
        channel: str = str(msg.channel)
        
        
        await sendMsg(msg,userMsg)
        
    client.run(tk)