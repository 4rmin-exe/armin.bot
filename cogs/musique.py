import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

FFMPEG_PATH = "ffmpeg"

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': '/tmp/%(id)s.%(ext)s',
}

FFMPEG_OPTIONS = {
    'options': '-vn'
}

class Musique(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def after_play(self, ctx, filepath):
        try:
            os.remove(filepath)
        except:
            pass
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            next_data = self.queues[ctx.guild.id].pop(0)
            source = discord.FFmpegOpusAudio(next_data['filepath'], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.after_play(ctx, next_data['filepath']))
            asyncio.run_coroutine_threadsafe(
                ctx.send(f"🎶 Au tour de : **{next_data['title']}**"),
                self.bot.loop
            )

    def download_audio(self, recherche: str):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"scsearch:{recherche}", download=True)['entries'][0]
                filepath = ydl.prepare_filename(info)
                return {'filepath': filepath, 'title': info['title']}
            except Exception:
                pass
            try:
                info = ydl.extract_info(f"ytsearch:{recherche}", download=True)['entries'][0]
                filepath = ydl.prepare_filename(info)
                return {'filepath': filepath, 'title': info['title']}
            except Exception:
                pass
        return None

    @commands.command(extras={"category": "Musique"})
    async def play(self, ctx, *, recherche: str = None):
        if not recherche:
            return await ctx.send("Dis-moi quoi jouer ! `+play <titre>`")
        if not ctx.author.voice:
            return await ctx.send("Tu dois être dans un salon vocal !")
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        msg = await ctx.send("🔍 Recherche en cours...")
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self.download_audio, recherche)
        if not data:
            return await msg.edit(content="Aucun résultat trouvé.")
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            if ctx.guild.id not in self.queues:
                self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append(data)
            await msg.edit(content=f"✅ Ajouté à la file : **{data['title']}**")
        else:
            source = discord.FFmpegOpusAudio(data['filepath'], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.after_play(ctx, data['filepath']))
            await msg.edit(content=f"🎶 En train de jouer : **{data['title']}**")

    @commands.command(extras={"category": "Musique"})
    async def queue(self, ctx):
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("La file d'attente est vide !")
        embed = discord.Embed(title="📋 File d'attente", color=0x00ff00)
        description = ""
        for i, music in enumerate(self.queues[ctx.guild.id], 1):
            description += f"{i}. **{music['title']}**\n"
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Musique"})
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Musique passée ⏩")

    @commands.command(extras={"category": "Musique"})
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queues[ctx.guild.id] = []
            ctx.voice_client.stop()
            await ctx.send("Musique arrêtée et file vidée.")

    @commands.command(extras={"category": "Musique"})
    async def leave(self, ctx):
        if ctx.voice_client:
            self.queues[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("Déconnecté ! 👋")

async def setup(bot):
    await bot.add_cog(Musique(bot))
