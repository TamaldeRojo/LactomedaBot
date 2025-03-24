import discord
from collections import deque
from lactomeda.config.constants import AltImgs

class MusicView(discord.ui.View): 
    def __init__(self, bot , server_configuration):
        super().__init__(timeout=None)
        self.bot = bot
        self.server_configuration = server_configuration
        music_channel_id = server_configuration.get("default_music_channel")
        self.default_music_channel = bot.get_channel(music_channel_id)
        self.embed_index = 0
        self.embeds = []
        self.message = None  
    
    async def send_initial_message(self, interaction):
        """Sends the initial embed and stores the message reference."""
        first_song = self.server_configuration["queue_songs"][0]
        initial_embed = await self.create_embeds(first_song)
        try:
            self.message = await interaction.followup.send(embed=initial_embed, view=self)
        except Exception as e:
            print(e)
            self.message = await self.default_music_channel.send(embed=initial_embed, view=self)

    async def create_embeds(self, song: deque = None, is_last_song: bool = False) -> discord.Embed:
        """Creates an embed for the currently playing song."""
        if is_last_song:
            last_embed = discord.Embed(
                title="🎵 La musica ha terminado",
                description="No hay más canciones en la cola",
                color=discord.Color.random()
            )
            self.pause.disabled = True
            self.resume.disabled = True
            self.stop.disabled = True
            self.skip_back.disabled = True
            self.skip_front.disabled = True
            self.view_queue.disabled = True
            self.shuffle_queue.disabled = True
            await self.update_message(last_embed)
            self.server_configuration["queue_songs"].clear()
            self.server_configuration["index_shuffle"].clear()
            self.server_configuration["is_shuffle"] = False
            self.server_configuration["current_index"] = -1
            return
        
        self.pause.disabled = False
        self.resume.disabled = True
        self.stop.disabled = False
        self.skip_back.disabled = False
        self.skip_front.disabled = False
        self.view_queue.disabled = False
            
        if self.message:
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{song['title']}**", #.get('title', 'Unknown') when i add more variables to the dict
                color=discord.Color.random()
            )
            embed.add_field(name="Artist", value=song.get('artist', 'Unknown'), inline=False)
            embed.add_field(name="Duration", value=song.get('duration', 'Unknown'), inline=True)
            embed.set_image(url=song.get('img_url', AltImgs.EMBED_ALT_IMG))
            
            #Needs to add a limit of titles to display btw
            queue_embed = discord.Embed(
                title="🎵 Queue",
                description="\n".join([f"**{song['title']}** - {song['artist']}" for song in self.server_configuration["queue_songs"]]),
                color=discord.Color.random()
            )
            self.embeds = [embed, queue_embed]
            return embed #for the initial embed
    
    async def update_message(self, last_embed: discord.Embed = None):
        if last_embed:
            await self.message.edit(embed=last_embed, view=self)
            return
        await self.message.edit(embed=self.embeds[self.embed_index], view=self)
        return self.embeds[self.embed_index]

    @discord.ui.button(label="Pausa", style=discord.ButtonStyle.gray)
    async def pause(self, button: discord.ui.Button, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            print("[+] Pausando la música")
            voice_client.pause()
            self.pause.disabled = True
            self.resume.disabled = False
            await interaction.response.edit_message(content="⏸️ Música Pausada",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser pausada",view=self)

    @discord.ui.button(label="Reanudar", style=discord.ButtonStyle.blurple)
    async def resume(self, button: discord.ui.Button, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            print("[+] Reanudando la música")
            voice_client.resume()
            self.pause.disabled = False
            self.resume.disabled = True
            await interaction.response.edit_message(content="▶️ Música Reanudada",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser reanudada",view=self)
            
            
    @discord.ui.button(label="Detener", style=discord.ButtonStyle.red)
    async def stop(self,  button: discord.ui.Button, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            
            print("[+] Quitando la música")
            self.server_configuration["is_stopped"] = True
            self.server_configuration["current_index"] = -1
            self.server_configuration["queue_songs"].clear()
            
            await self.update_message(self.embeds[1])
            voice_client.stop()
            self.embeds[0].clear_fields()
            await voice_client.disconnect()
            
            await interaction.response.edit_message(content="❌ Música Detenida, no hay nada en la lista",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser detenida",view=self)
            
    @discord.ui.button(label="<<", style=discord.ButtonStyle.gray, row=1)
    async def skip_back(self,  button: discord.ui.Button, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            print("[+] Reproduciendo la música anterior")
            voice_client.stop()
            if not self.server_configuration["is_shuffle"]:
                self.server_configuration["current_index"] -= 2 # 2 pq se va a sumar despues 1
                if self.server_configuration["current_index"] < -1:
                    self.server_configuration["current_index"] = -1
            else:
                self.server_configuration["is_back_skip"] = True
                self.server_configuration["index_shuffle"].pop()
                self.server_configuration["current_index"] = self.server_configuration["index_shuffle"].pop()
            await interaction.response.edit_message(content="✔ Reproduciendo la música anterior",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser Adelantada",view=self)


    @discord.ui.button(label=">>", style=discord.ButtonStyle.gray, row=1)
    async def skip_front(self,  button: discord.ui.Button, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            print("[+] Saltando la música")
            voice_client.stop()
            await interaction.response.edit_message(content="✔ Reproduciendo la música siguiente",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser Adelantada",view=self)

    @discord.ui.button(label="Aleatorio", style=discord.ButtonStyle.gray, row=1)
    async def shuffle_queue(self,  button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.server_configuration["queue_songs"]) > 0:
            self.server_configuration["is_shuffle"] = True
            last_song_indexes = list(range(self.server_configuration["current_index"] + 1))
            for index in last_song_indexes:
                self.server_configuration["index_shuffle"].append(index)
            await interaction.response.edit_message(content="Musica en cola en modo aleatorio",view=self)
        else:
            await interaction.response.edit_message(content="❌ Trabajo en ello okay?",view=self)

    
    
    @discord.ui.button(label="🔲", style=discord.ButtonStyle.gray, row=1)
    async def view_queue(self,  button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.server_configuration["queue_songs"]) > 0:
            await interaction.response.edit_message(content="En progreso...",view=self)
        else:
            await interaction.response.edit_message(content="❌ Trabajo en ello okay?",view=self)
