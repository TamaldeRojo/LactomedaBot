import discord
from collections import deque

from lactomeda.config.constants import AltImgs

class MusicView(discord.ui.View): 
    def __init__(self, bot ,queue_songs: deque, current_index: list, is_stopped: list):
        super().__init__(timeout=None)
        self.is_stopped = is_stopped
        self.bot = bot
        self.queue_songs = queue_songs
        self.current_index = current_index
        self.embed_index = 0
        self.embeds = []
        self.message = None  
    
    async def send_initial_message(self, interaction: discord.Interaction):
        """Sends the initial embed and stores the message reference."""
        first_song = self.queue_songs[0]
        initial_embed = await self.create_embeds(first_song)
        self.message = await interaction.followup.send(embed=initial_embed, view=self)

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
            await self.update_message(last_embed)
            self.queue_songs.clear()
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
            
            queue_embed = discord.Embed(
                title="🎵 Queue",
                description="\n".join([f"**{song['title']}** - {song['artist']}" for song in self.queue_songs]),
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
            self.is_stopped[0] = True
            self.current_index[0] = -1
            
            self.queue_songs.clear()
            voice_client.stop()
            self.embed.clear_fields()
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
            self.current_index[0] -= 2 # 2 pq se va a sumar despues 1
            if self.current_index[0] < -1:
                self.current_index[0] = -1
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

    @discord.ui.button(label="🔲", style=discord.ButtonStyle.gray, row=1)
    async def view_queue(self,  button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.queue_songs) > 0:
            await interaction.response.edit_message(content="✔ Reproduciendo la música siguiente",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser Adelantada",view=self)
