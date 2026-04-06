import discord
from discord.ext import commands
from database import get_logs, set_log

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, categorie, embed):
        log_channels = get_logs(str(guild.id))
        salon_id = log_channels.get(categorie)
        if not salon_id:
            return
        salon = guild.get_channel(salon_id)
        if salon:
            await salon.send(embed=embed)

    @commands.command(extras={"category": "Permissions & Logs"})
    async def setlog(self, ctx, categorie: str = None, salon: discord.TextChannel = None):
        if not categorie or not salon:
            await ctx.send("Utilise `+setlog <catégorie> #salon`\nCatégories : `messages`, `membres`, `vocal`, `moderation`, `salons`, `roles`, `boosts`, `tickets`")
            return
        categories_valides = ["messages", "membres", "vocal", "moderation", "salons", "roles", "boosts", "tickets"]
        if categorie not in categories_valides:
            await ctx.send(f"Catégorie invalide. Choisis parmi : {', '.join(categories_valides)}")
            return
        set_log(str(ctx.guild.id), categorie, salon.id)
        await ctx.send(f"Logs `{categorie}` configurés dans {salon.mention}.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def loglist(self, ctx):
        log_channels = get_logs(str(ctx.guild.id))
        if not log_channels:
            await ctx.send("Aucun salon de logs configuré.")
            return
        embed = discord.Embed(title="Salons de logs", color=0x00ff00)
        for cat, salon_id in log_channels.items():
            salon = ctx.guild.get_channel(salon_id)
            embed.add_field(name=cat, value=salon.mention if salon else "Salon introuvable", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        embed = discord.Embed(title="Message supprimé", color=0xff0000)
        embed.add_field(name="Auteur", value=message.author.mention)
        embed.add_field(name="Salon", value=message.channel.mention)
        embed.add_field(name="Contenu", value=message.content or "Aucun contenu", inline=False)
        await self.send_log(message.guild, "messages", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        embed = discord.Embed(title="Message modifié", color=0xffaa00)
        embed.add_field(name="Auteur", value=before.author.mention)
        embed.add_field(name="Salon", value=before.channel.mention)
        embed.add_field(name="Avant", value=before.content or "Aucun contenu", inline=False)
        embed.add_field(name="Après", value=after.content or "Aucun contenu", inline=False)
        await self.send_log(before.guild, "messages", embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title="Membre arrivé", color=0x00ff00)
        embed.add_field(name="Membre", value=member.mention)
        embed.add_field(name="ID", value=str(member.id))
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, "membres", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title="Membre parti", color=0xff0000)
        embed.add_field(name="Membre", value=str(member))
        embed.add_field(name="ID", value=str(member.id))
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.send_log(member.guild, "membres", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            embed = discord.Embed(title="Pseudo modifié", color=0xffff00)
            embed.add_field(name="Membre", value=after.mention)
            embed.add_field(name="Ancien pseudo", value=before.nick or before.name)
            embed.add_field(name="Nouveau pseudo", value=after.nick or after.name)
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                    if entry.target.id == after.id and entry.user.id != after.id:
                        embed.add_field(name="Modifié par", value=f"{entry.user.mention} (ID: {entry.user.id})")
            except:
                pass
            await self.send_log(after.guild, "membres", embed)

        roles_ajoutes = [r for r in after.roles if r not in before.roles]
        roles_retires = [r for r in before.roles if r not in after.roles]
        if roles_ajoutes:
            embed = discord.Embed(title="Rôle ajouté", color=0x00ff00)
            embed.add_field(name="Membre", value=after.mention)
            embed.add_field(name="Rôle", value=roles_ajoutes[0].mention)
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    embed.add_field(name="Par", value=f"{entry.user.mention} (ID: {entry.user.id})")
            except:
                pass
            await self.send_log(after.guild, "roles", embed)
        if roles_retires:
            embed = discord.Embed(title="Rôle retiré", color=0xff0000)
            embed.add_field(name="Membre", value=after.mention)
            embed.add_field(name="Rôle", value=roles_retires[0].mention)
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    embed.add_field(name="Par", value=f"{entry.user.mention} (ID: {entry.user.id})")
            except:
                pass
            await self.send_log(after.guild, "roles", embed)

        if before.premium_since is None and after.premium_since is not None:
            embed = discord.Embed(title="Nouveau boost", color=0xff69b4)
            embed.add_field(name="Membre", value=after.mention)
            embed.set_thumbnail(url=after.display_avatar.url)
            await self.send_log(after.guild, "boosts", embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(title="Entrée vocale", color=0x00ff00)
            embed.add_field(name="Membre", value=member.mention)
            embed.add_field(name="Salon", value=after.channel.name)
            await self.send_log(member.guild, "vocal", embed)
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(title="Sortie vocale", color=0xff0000)
            embed.add_field(name="Membre", value=member.mention)
            embed.add_field(name="Salon", value=before.channel.name)
            await self.send_log(member.guild, "vocal", embed)
        elif before.channel != after.channel:
            embed = discord.Embed(title="Déplacement vocal", color=0xffaa00)
            embed.add_field(name="Membre", value=member.mention)
            embed.add_field(name="Avant", value=before.channel.name)
            embed.add_field(name="Après", value=after.channel.name)
            await self.send_log(member.guild, "vocal", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="Salon créé", color=0x00ff00)
        embed.add_field(name="Salon", value=channel.mention)
        embed.add_field(name="Type", value=str(channel.type))
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                embed.add_field(name="Créé par", value=f"{entry.user.mention} (ID: {entry.user.id})")
        except:
            pass
        await self.send_log(channel.guild, "salons", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="Salon supprimé", color=0xff0000)
        embed.add_field(name="Nom", value=channel.name)
        embed.add_field(name="Type", value=str(channel.type))
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                embed.add_field(name="Supprimé par", value=f"{entry.user.mention} (ID: {entry.user.id})")
        except:
            pass
        await self.send_log(channel.guild, "salons", embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))