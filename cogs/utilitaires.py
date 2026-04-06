import discord
from discord.ext import commands

class Utilitaires(commands.Cog):  
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Utilitaires(bot))  

    import discord
from discord.ext import commands
import math
import wikipedia
import aiohttp
import time
from openai import AsyncOpenAI
import re
import io

OPENROUTER_KEY = "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"
UNSPLASH_KEY = "OayD9SavOGmQ9FF5qUAP5ynkjgjVgQnRRdIavCsy6co"

ai_client = AsyncOpenAI(
    api_key=OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1"
)

class Utilitaires(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(extras={"category": "Utilitaires"})
    async def pic(self, ctx, membre: discord.Member = None):
        membre = membre or ctx.author
        await ctx.send(membre.display_avatar.url)

    @commands.command(extras={"category": "Utilitaires"})
    async def banner(self, ctx, membre: discord.Member = None):
        membre = membre or ctx.author
        user = await self.bot.fetch_user(membre.id)
        if user.banner:
            await ctx.send(user.banner.url)
        else:
            await ctx.send("Cet utilisateur n'a pas de bannière.")

    @commands.command(extras={"category": "Utilitaires"})
    async def serverpic(self, ctx):
        if ctx.guild.icon:
            await ctx.send(ctx.guild.icon.url)
        else:
            await ctx.send("Ce serveur n'a pas d'icône.")

    @commands.command(extras={"category": "Utilitaires"})
    async def serverbanner(self, ctx):
        if ctx.guild.banner:
            await ctx.send(ctx.guild.banner.url)
        else:
            await ctx.send("Ce serveur n'a pas de bannière.")

    @commands.command(extras={"category": "Utilitaires"})
    async def calc(self, ctx, *, calcul: str):
        try:
            resultat = eval(calcul, {"__builtins__": {}}, {"sqrt": math.sqrt, "pi": math.pi})
            await ctx.send(f"Résultat : `{resultat}`")
        except:
            await ctx.send("Calcul invalide.")

    @commands.command(extras={"category": "Utilitaires"})
    async def wiki(self, ctx, *, recherche: str):
        try:
            wikipedia.set_lang("fr")
            resume = wikipedia.summary(recherche, sentences=3)
            if len(resume) > 2000:
                resume = resume[:1997] + "..."
            await ctx.send(resume)
        except:
            await ctx.send("Aucun résultat trouvé.")

    @commands.command(extras={"category": "Utilitaires"})
    async def ai(self, ctx, *, question: str = None):
        if not question:
            await ctx.send("Pose une question. Ex: `+ai c'est quoi Python ?`")
            return
        async with ctx.typing():
            try:
                reponse = await ai_client.chat.completions.create(
                    model="google/gemma-3n-e4b-it:free",
                    messages=[{"role": "user", "content": question}]
                )
                texte = reponse.choices[0].message.content
                if len(texte) > 2000:
                    morceaux = [texte[i:i+2000] for i in range(0, len(texte), 2000)]
                    for morceau in morceaux:
                        await ctx.send(morceau)
                else:
                    await ctx.send(texte)
            except Exception as e:
                await ctx.send(f"Erreur : {e}")

    @commands.command(extras={"category": "Utilitaires"})
    async def image(self, ctx, *, recherche: str = None):
        if not recherche:
            await ctx.send("Utilise `+image <mot-clé>`")
            return
        async with aiohttp.ClientSession() as session:
            url = f"https://api.unsplash.com/photos/random?query={recherche}&client_id={UNSPLASH_KEY}"
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Aucun résultat trouvé.")
                    return
                data = await resp.json()
                image_url = data["urls"]["regular"]
                auteur = data["user"]["name"]
                embed = discord.Embed(title=f"Résultat pour : {recherche}", color=0x00ff00)
                embed.set_image(url=image_url)
                embed.set_footer(text=f"Photo par {auteur} sur Unsplash")
                await ctx.send(embed=embed)

    @commands.command(extras={"category": "Utilitaires"})
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message: str = None):
        if not message:
            await ctx.send("Écris un message après la commande. Ex: `+say bonjour`")
            return
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(extras={"category": "Utilitaires"})
    @commands.has_permissions(manage_emojis=True)
    async def emoji(self, ctx, emojii: str = None):
        if not emojii:
            await ctx.send("Utilise `+emoji <emoji>`")
            return
        match = re.match(r'<a?:(\w+):(\d+)>', emojii)
        if not match:
            await ctx.send("Ce n'est pas un emoji custom. Ça ne marche qu'avec les emojis de serveurs Discord.")
            return
        nom = match.group(1)
        emoji_id = match.group(2)
        animated = emojii.startswith("<a:")
        ext = "gif" if animated else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Impossible de récupérer l'emoji.")
                    return
                image = await resp.read()
        try:
            nouvel_emoji = await ctx.guild.create_custom_emoji(name=nom, image=image)
            await ctx.send(f"Emoji ajouté : {nouvel_emoji}")
        except discord.Forbidden:
            await ctx.send("Je n'ai pas la permission d'ajouter des emojis.")
        except discord.HTTPException as e:
            await ctx.send(f"Erreur : {e}")

    @commands.command(extras={"category": "Utilitaires"})
    @commands.has_permissions(manage_emojis=True)
    async def sticker(self, ctx, *, nom: str = None):
        if not ctx.message.stickers:
            await ctx.send("Envoie un sticker avec la commande. Ex: `+sticker` + sticker joint")
            return
        sticker_source = ctx.message.stickers[0]
        if nom is None:
            nom = sticker_source.name
        url = str(sticker_source.url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Impossible de récupérer le sticker.")
                    return
                image = await resp.read()
        try:
            nouveau_sticker = await ctx.guild.create_sticker(
                name=nom,
                description=nom,
                emoji="⭐",
                file=discord.File(fp=io.BytesIO(image), filename=f"{nom}.png")
            )
            await ctx.send(f"Sticker ajouté : **{nouveau_sticker.name}**")
        except discord.Forbidden:
            await ctx.send("Je n'ai pas la permission d'ajouter des stickers.")
        except discord.HTTPException as e:
            await ctx.send(f"Erreur : {e}")

    @commands.command(extras={"category": "Utilitaires"})
    async def userinfo(self, ctx, membre: discord.Member = None):
        membre = membre or ctx.author
        roles = [r.mention for r in membre.roles if r.name != "@everyone"]
        embed = discord.Embed(title=f"Infos — {membre}", color=membre.color)
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="ID", value=str(membre.id))
        embed.add_field(name="Pseudo", value=membre.display_name)
        embed.add_field(name="Compte créé le", value=membre.created_at.strftime("%d/%m/%Y"))
        embed.add_field(name="A rejoint le", value=membre.joined_at.strftime("%d/%m/%Y"))
        embed.add_field(name="Rôles", value=" ".join(roles) if roles else "Aucun", inline=False)
        embed.add_field(name="Bot ?", value="Oui" if membre.bot else "Non")
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Utilitaires"})
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=f"Infos — {guild.name}", color=0x00ff00)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=str(guild.id))
        embed.add_field(name="Propriétaire", value=str(guild.owner))
        embed.add_field(name="Membres", value=str(guild.member_count))
        embed.add_field(name="Salons texte", value=str(len(guild.text_channels)))
        embed.add_field(name="Salons vocaux", value=str(len(guild.voice_channels)))
        embed.add_field(name="Rôles", value=str(len(guild.roles)))
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count))
        embed.add_field(name="Niveau boost", value=str(guild.premium_tier))
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"))
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Utilitaires"})
    async def roleinfo(self, ctx, role: discord.Role = None):
        if not role:
            await ctx.send("Mentionne un rôle. Ex: `+roleinfo @Modérateur`")
            return
        membres = [m for m in ctx.guild.members if role in m.roles]
        perms = [p[0] for p in role.permissions if p[1]]
        perms_str = ", ".join(perms[:5]) + ("..." if len(perms) > 5 else "") if perms else "Aucune"
        embed = discord.Embed(title=f"Infos — {role.name}", color=role.color)
        embed.add_field(name="ID", value=str(role.id))
        embed.add_field(name="Couleur", value=str(role.color))
        embed.add_field(name="Membres", value=str(len(membres)))
        embed.add_field(name="Mentionnable", value="Oui" if role.mentionable else "Non")
        embed.add_field(name="Séparé dans la liste", value="Oui" if role.hoist else "Non")
        embed.add_field(name="Créé le", value=role.created_at.strftime("%d/%m/%Y"))
        embed.add_field(name="Permissions clés", value=perms_str, inline=False)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Utilitaires"})
    async def ping(self, ctx):
        latence = round(self.bot.latency * 1000)
        couleur = 0x00ff00 if latence < 100 else 0xffaa00 if latence < 200 else 0xff0000
        embed = discord.Embed(title="🏓 Pong !", color=couleur)
        embed.add_field(name="Latence", value=f"{latence} ms")
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Utilitaires"})
    async def botinfo(self, ctx):
        latence = round(self.bot.latency * 1000)
        uptime_secondes = int(time.time() - self.bot.start_time) if self.bot.start_time else 0
        heures, reste = divmod(uptime_secondes, 3600)
        minutes, secondes = divmod(reste, 60)
        uptime_str = f"{heures}h {minutes}m {secondes}s"
        nb_serveurs = len(self.bot.guilds)
        nb_membres = sum(g.member_count for g in self.bot.guilds)
        nb_commandes = len(self.bot.commands)
        embed = discord.Embed(title=f"Infos — {self.bot.user.name}", color=0x00ff00)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Latence", value=f"{latence} ms")
        embed.add_field(name="Uptime", value=uptime_str)
        embed.add_field(name="Serveurs", value=str(nb_serveurs))
        embed.add_field(name="Membres totaux", value=str(nb_membres))
        embed.add_field(name="Commandes", value=str(nb_commandes))
        embed.add_field(name="Préfixe", value="+")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilitaires(bot))