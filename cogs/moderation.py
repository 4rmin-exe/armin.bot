import discord
from discord.ext import commands
import asyncio
from database import get_warns, set_warns, set_prefix

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, categorie, embed):
        logs_cog = self.bot.get_cog("Logs")
        if logs_cog:
            await logs_cog.send_log(guild, categorie, embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, membre: discord.Member = None, *, raison="Aucune raison"):
        if not membre:
            await ctx.send("Mentionne un membre à kick.")
            return
        await membre.kick(reason=raison)
        embed = discord.Embed(title="Membre kick", color=0xff6600)
        embed.add_field(name="Membre", value=str(membre))
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=str(ctx.author))
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "moderation", embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, membre: discord.Member = None, *, raison="Aucune raison"):
        if not membre:
            await ctx.send("Mentionne un membre à bannir.")
            return
        await membre.ban(reason=raison)
        embed = discord.Embed(title="Membre banni", color=0xff0000)
        embed.add_field(name="Membre", value=str(membre))
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=str(ctx.author))
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "moderation", embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, nom: str):
        bans = [entry async for entry in ctx.guild.bans()]
        for entry in bans:
            if str(entry.user) == nom:
                await ctx.guild.unban(entry.user)
                embed = discord.Embed(title="Membre débanni", color=0x00ff00)
                embed.add_field(name="Membre", value=nom)
                embed.add_field(name="Modérateur", value=str(ctx.author))
                await ctx.send(embed=embed)
                await self.send_log(ctx.guild, "moderation", embed)
                return
        await ctx.send("Utilisateur introuvable dans les bans.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, membre: discord.Member = None, *, raison="Aucune raison"):
        if not membre:
            await ctx.send("Mentionne un membre à mute.")
            return
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        await membre.add_roles(role)
        embed = discord.Embed(title="Membre mute", color=0xffff00)
        embed.add_field(name="Membre", value=str(membre))
        embed.add_field(name="Raison", value=raison)
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "moderation", embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, membre: discord.Member = None):
        if not membre:
            await ctx.send("Mentionne un membre à unmute.")
            return
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if role and role in membre.roles:
            await membre.remove_roles(role)
            await ctx.send(f"{membre} a été unmute.")
        else:
            await ctx.send("Ce membre n'est pas mute.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_roles=True)
    async def tempmute(self, ctx, membre: discord.Member = None, duree: str = None, *, raison="Aucune raison"):
        if not membre or not duree:
            await ctx.send("Utilise `+tempmute @membre <durée> <raison>`. Ex: `+tempmute @user 10m spam`")
            return
        unites = {"s": 1, "m": 60, "h": 3600, "j": 86400}
        unite = duree[-1].lower()
        if unite not in unites or not duree[:-1].isdigit():
            await ctx.send("Durée invalide. Utilise `s`, `m`, `h`, `j`. Ex: `10m`")
            return
        secondes = int(duree[:-1]) * unites[unite]
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        await membre.add_roles(role)
        embed = discord.Embed(title="Membre tempmute", color=0xffff00)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Durée", value=duree)
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=ctx.author.mention)
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "moderation", embed)
        await asyncio.sleep(secondes)
        if role in membre.roles:
            await membre.remove_roles(role)
            await ctx.send(f"{membre.mention} a été unmute automatiquement.")

    @commands.command(name="clear", extras={"category": "Modération"})
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, nombre: str = "10"):
        if nombre.lower() == "all":
            await ctx.channel.purge(limit=None)
            await ctx.send("Tous les messages ont été supprimés.", delete_after=3)
        else:
            try:
                n = int(nombre)
                await ctx.channel.purge(limit=n + 1)
                await ctx.send(f"{n} messages supprimés.", delete_after=3)
            except ValueError:
                await ctx.send("Utilise `+clear <nombre>` ou `+clear all`.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, membre: discord.Member = None, *, raison="Aucune raison"):
        if not membre:
            await ctx.send("Mentionne un membre à avertir.")
            return
        total = get_warns(str(membre.id)) + 1
        set_warns(str(membre.id), total)
        embed = discord.Embed(title="Avertissement", color=0xffaa00)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Modérateur", value=ctx.author.mention)
        embed.add_field(name="Total warns", value=str(total))
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "moderation", embed)
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        if total == 3:
            await membre.add_roles(role)
            await ctx.send(f"{membre.mention} a reçu 3 warns — mute de 30 secondes.")
            await asyncio.sleep(30)
            if role in membre.roles:
                await membre.remove_roles(role)
        elif total == 6:
            await membre.add_roles(role)
            await ctx.send(f"{membre.mention} a reçu 6 warns — mute de 2 minutes.")
            await asyncio.sleep(120)
            if role in membre.roles:
                await membre.remove_roles(role)
        elif total >= 10:
            await membre.kick(reason="10 warns atteints")
            await ctx.send(f"{membre.mention} a été kick — 10 warns atteints.")
            set_warns(str(membre.id), 0)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_messages=True)
    async def warncheck(self, ctx, membre: discord.Member = None):
        if not membre:
            await ctx.send("Mentionne un membre.")
            return
        total = get_warns(str(membre.id))
        await ctx.send(f"{membre.mention} a **{total} warn(s)**.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_messages=True)
    async def clearwarns(self, ctx, membre: discord.Member = None):
        if not membre:
            await ctx.send("Mentionne un membre.")
            return
        set_warns(str(membre.id), 0)
        await ctx.send(f"Warns de {membre.mention} réinitialisés.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, membre: discord.Member = None, role: discord.Role = None):
        if not membre or not role:
            await ctx.send("Utilise `+addrole @membre @role`")
            return
        if role in membre.roles:
            await ctx.send(f"{membre.mention} a déjà le rôle {role.mention}.")
            return
        await membre.add_roles(role)
        embed = discord.Embed(title="Rôle ajouté", color=0x00ff00)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Rôle", value=role.mention)
        embed.add_field(name="Modérateur", value=ctx.author.mention)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, membre: discord.Member = None, role: discord.Role = None):
        if not membre or not role:
            await ctx.send("Utilise `+removerole @membre @role`")
            return
        if role not in membre.roles:
            await ctx.send(f"{membre.mention} n'a pas le rôle {role.mention}.")
            return
        await membre.remove_roles(role)
        embed = discord.Embed(title="Rôle retiré", color=0xff0000)
        embed.add_field(name="Membre", value=membre.mention)
        embed.add_field(name="Rôle", value=role.mention)
        embed.add_field(name="Modérateur", value=ctx.author.mention)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await salon.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(f"Salon {salon.mention} caché.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await salon.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send(f"Salon {salon.mention} visible.")

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await salon.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(title="🔒 Salon verrouillé", color=0xff0000)
        embed.add_field(name="Salon", value=salon.mention)
        embed.add_field(name="Par", value=ctx.author.mention)
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "salons", embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, salon: discord.TextChannel = None):
        salon = salon or ctx.channel
        await salon.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(title="🔓 Salon déverrouillé", color=0x00ff00)
        embed.add_field(name="Salon", value=salon.mention)
        embed.add_field(name="Par", value=ctx.author.mention)
        await ctx.send(embed=embed)
        await self.send_log(ctx.guild, "salons", embed)

    @commands.command(extras={"category": "Modération"})
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, secondes: int = None):
        if secondes is None:
            await ctx.send("Utilise `+slowmode <secondes>` ou `+slowmode 0` pour désactiver.")
            return
        if secondes < 0 or secondes > 21600:
            await ctx.send("La durée doit être entre 0 et 21600 secondes.")
            return
        await ctx.channel.edit(slowmode_delay=secondes)
        if secondes == 0:
            await ctx.send("Slowmode désactivé.")
        else:
            await ctx.send(f"Slowmode activé : {secondes} seconde(s).")

    @commands.command(extras={"category": "Modération"})
    async def setprefix(self, ctx, nouveau: str = None):
        perms_cog = self.bot.get_cog("Permissions")
        if not perms_cog or ctx.author.id not in perms_cog.owner_ids:
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nouveau:
            await ctx.send("Indique un préfixe. Ex: `+setprefix !`")
            return
        if len(nouveau) > 3:
            await ctx.send("Le préfixe doit faire 3 caractères maximum.")
            return
        set_prefix(str(ctx.guild.id), nouveau)
        self.bot.command_prefix = lambda bot, msg: set_prefix
        await ctx.send(f"Préfixe changé en `{nouveau}`")

async def setup(bot):
    await bot.add_cog(Moderation(bot))