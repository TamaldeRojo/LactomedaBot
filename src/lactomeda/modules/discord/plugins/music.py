import random, hikari, crescent



plugin = crescent.Plugin[hikari.GatewayBot, None]()


@plugin.include
@crescent.command(name="play", description="Pega el nombre o la url de la canción")
class Play:
    
    async def callback(self, ctx: crescent.Context) -> None:
      
     
        await ctx.respond(
           
        )