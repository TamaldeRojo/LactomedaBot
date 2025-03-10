import discord
from collections import deque

class MusicView(discord.ui.View): 
    def __init__(self, client ,queue_songs: deque):
        super().__init__()
        self.client = client
        self.queue_songs = queue_songs

    @discord.ui.button(label="Pausa", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[+] Pausando la música")
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.edit_message(content="⏸️ Música Pausada",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser pausada",view=self)

    @discord.ui.button(label="Reanudar", style=discord.ButtonStyle.blurple)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[+] Reanudando la música")
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.edit_message(content="▶️ Música Reanudada",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser reanudada",view=self)

    @discord.ui.button(label="Detener", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[+] Quitando la música")
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            self.queue_songs.clear()
            await interaction.response.edit_message(content="❌ Música Detenida, no hay nada en la lista",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser detenida",view=self)
