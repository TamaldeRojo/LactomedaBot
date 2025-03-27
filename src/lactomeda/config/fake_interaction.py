import discord
from discord import InteractionType
from lactomeda.config.lactomeda_config import LactomedaConfig
# Create a fake interaction to execute the slash commands xd

lactomeda_setup = LactomedaConfig.get_instance()


class FakeInteraction(discord.Interaction):
    def __init__(self, bot, message):
        
        lactomeda_setup.get_server_config(message.guild.id)
        data = {
            "id": message.id,  # Use the message ID or any unique identifier
            "type": InteractionType.application_command,  # Type of interaction (e.g., slash command)
            "guild_id": message.guild.id if message.guild else None,
            "version":1,# Guild ID, or None for DMs
            "channel_id": message.channel.id,  # Channel ID where the interaction was triggered
            "application_id": bot.user.id,  # Application ID (your bot's ID)
            "user": {"id": message.author.id, "username": message.author.name, "discriminator": message.author.discriminator},  # User details
            "token": "fake_token_123456",  # Fake token to continue interaction
            "data": {
                "name": "play",  # Command name (replace with the actual command name you are simulating)
                "type": 2  # Interaction type (1 for slash commands)
            },
            # "locale": "en-US",  # User's locale
            # "guild_locale": "en-US"  # Guild's preferred locale, if applicable
        }
        super().__init__(data=data, state=bot._connection)
        self.bot = bot
        self._guild = message.guild
        self.channel = message.channel
        self.user = message.author
        self.response = FakeResponse(self)
    
    async def response_defer(self):
        pass  # Simulate interaction defer
   
    
class FakeResponse(discord.InteractionResponse):
    def __init__(self,interaction):
        super().__init__(interaction)

  