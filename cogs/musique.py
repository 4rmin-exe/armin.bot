import discord
from discord.ext import commands

class Musique(commands.Cog):  
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Musique(bot))  

    import discord
from discord.ext import commands
import yt_dlp
import asyncio

FFMPEG_PATH = r"C:\Users\Daniel\Desktop\Danny\armin.bot\app\ffmpeg-2026-04-01-git-eedf8f0165-full_build\ffmpeg-2026-04-01-git-eedf8f0165-full_build\bin\ffmpeg.exe"

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class Musique(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def check_queue(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            next_source = self.queues[ctx.guild.id].pop(0)
            source = discord.FFmpegOpusAudio(next_source['url'], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.check_queue(ctx))
            asyncio.run_coroutine_threadsafe(
                ctx.send(f"🎶 Au tour de : **{next_source['title']}**"),
                self.bot.loop
            )

    @commands.command(extras={"category": "Musique"})
    async def play(self, ctx, *, recherche: str = None):
        if not recherche:
            return await ctx.send("Dis-moi quoi jouer ! `+play <titre>`")
        if not ctx.author.voice:
            return await ctx.send("Tu dois être dans un salon vocal !")
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(f"ytsearch:{recherche}", download=False)['entries'][0]
                    data = {'url': info['url'], 'title': info['title']}
                except Exception as e:
                    return await ctx.send(f"Erreur de recherche : {e}")
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            if ctx.guild.id not in self.queues:
                self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append(data)
            await ctx.send(f"✅ Ajouté à la file : **{data['title']}**")
        else:
            source = await discord.FFmpegOpusAudio.from_probe(data['url'], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.check_queue(ctx))
            await ctx.send(f"🎶 En train de jouer : **{data['title']}**")

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