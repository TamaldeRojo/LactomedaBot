import discord
from collections import deque

class MusicView(discord.ui.View): 
    def __init__(self, client ,queue_songs: deque, current_index: list, is_stopped: list):
        super().__init__(timeout=None)
        self.is_stopped = is_stopped
        self.client = client
        self.queue_songs = queue_songs
        self.current_index = current_index

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
            
            self.is_stopped[0] = True
            self.current_index[0] = -1
            
            self.queue_songs.clear()
            voice_client.stop()
            
            await interaction.response.edit_message(content="❌ Música Detenida, no hay nada en la lista",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser detenida",view=self)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.gray)
    async def skip_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[+] Reproduciendo la música anterior")
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            self.current_index[0] -= 2 # 2 pq se va a sumar despues 1
            if self.current_index[0] < -1:
                self.current_index[0] = -1
            await interaction.response.edit_message(content="✔ Reproduciendo la música anterior",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser Adelantada",view=self)


    @discord.ui.button(label=">>", style=discord.ButtonStyle.gray)
    async def skip_front(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[+] Saltando la música")
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.edit_message(content="✔ Reproduciendo la música siguiente",view=self)
        else:
            await interaction.response.edit_message(content="❌ La musica no pudo ser Adelantada",view=self)

