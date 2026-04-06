import discord
from discord.ext import commands
import asyncio
from database import get_tickets, set_ticket_role, open_ticket, close_ticket

class TicketSelect(discord.ui.Select):
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="Owner", description="Contacter les owners", emoji="👑"),
            discord.SelectOption(label="Staff", description="Contacter le staff", emoji="🛡️"),
            discord.SelectOption(label="Abus", description="Signaler un abus", emoji="⚠️"),
            discord.SelectOption(label="Questions", description="Poser une question", emoji="❓"),
            discord.SelectOption(label="Autres", description="Autre sujet", emoji="📩"),
        ]
        super().__init__(placeholder="Choisis une catégorie...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        categorie = self.values[0]
        guild = interaction.guild
        membre = interaction.user
        tickets_data = get_tickets(str(guild.id))

        open_tickets = tickets_data.get("open", {})
        if str(membre.id) in open_tickets:
            salon_id = open_tickets[str(membre.id)]
            salon = guild.get_channel(int(salon_id))
            if salon:
                await interaction.followup.send(
                    f"Tu as déjà un ticket ouvert : {salon.mention}", ephemeral=True
                )
                return

        nom_categorie = f"Tickets — {categorie}"
        categorie_discord = discord.utils.get(guild.categories, name=nom_categorie)
        if not categorie_discord:
            categorie_discord = await guild.create_category(nom_categorie)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            membre: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        roles_config = tickets_data.get("roles", {})
        role_id = roles_config.get(categorie.lower())
        role_ping = None
        if role_id:
            role_ping = guild.get_role(int(role_id))
            if role_ping:
                overwrites[role_ping] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        perms_cog = self.bot.get_cog("Permissions")
        if perms_cog:
            for owner_id in perms_cog.owner_ids:
                owner = guild.get_member(owner_id)
                if owner:
                    overwrites[owner] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        nom_salon = f"ticket-{membre.name}".lower().replace(" ", "-")
        salon = await guild.create_text_channel(
            name=nom_salon,
            category=categorie_discord,
            overwrites=overwrites
        )

        open_ticket(str(guild.id), str(membre.id), salon.id)

        embed = discord.Embed(
            title=f"Ticket — {categorie}",
            description=f"Bienvenue {membre.mention} ! Explique ton problème, l'équipe va te répondre.",
            color=0x00ff00
        )
        embed.set_footer(text=f"Ticket ouvert par {membre} | Catégorie : {categorie}")
        await salon.send(embed=embed)

        mentions = []
        if role_ping:
            mentions.append(role_ping.mention)
        mentions.append(membre.mention)
        ping_msg = await salon.send(" ".join(mentions))
        await asyncio.sleep(1)
        await ping_msg.delete()

        await interaction.followup.send(
            f"Ton ticket a été créé : {salon.mention}", ephemeral=True
        )

class TicketView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.add_item(TicketSelect(bot, guild_id))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(extras={"category": "Permissions & Logs"})
    async def ticket(self, ctx):
        embed = discord.Embed(
            title="Ouvrir un ticket",
            description="Sélectionne une catégorie dans le menu ci-dessous.",
            color=0x00ff00
        )
        await ctx.send(embed=embed, view=TicketView(self.bot, str(ctx.guild.id)))

    @commands.command(extras={"category": "Permissions & Logs"})
    async def setticket(self, ctx, categorie: str = None, role: discord.Role = None):
        perms_cog = self.bot.get_cog("Permissions")
        if not perms_cog or ctx.author.id not in perms_cog.owner_ids:
            await ctx.send("Tu n'as pas la permission.")
            return
        if not categorie or not role:
            await ctx.send("Utilise `+setticket <categorie> @role`\nCatégories : `owner`, `staff`, `abus`, `questions`, `autres`")
            return
        categories_valides = ["owner", "staff", "abus", "questions", "autres"]
        if categorie.lower() not in categories_valides:
            await ctx.send(f"Catégorie invalide. Choisis parmi : {', '.join(categories_valides)}")
            return
        set_ticket_role(str(ctx.guild.id), categorie.lower(), role.id)
        await ctx.send(f"Rôle {role.mention} configuré pour la catégorie `{categorie}`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def closeticket(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            await ctx.send("Cette commande ne fonctionne que dans un salon de ticket.")
            return

        perms_cog = self.bot.get_cog("Permissions")
        est_owner = perms_cog and ctx.author.id in perms_cog.owner_ids

        tickets_data = get_tickets(str(ctx.guild.id))
        roles_config = tickets_data.get("roles", {})
        est_autorise = est_owner

        if not est_autorise:
            for role_id in roles_config.values():
                role = ctx.guild.get_role(int(role_id))
                if role and role in ctx.author.roles:
                    est_autorise = True
                    break

        open_tickets = tickets_data.get("open", {})
        for membre_id, salon_id in open_tickets.items():
            if int(salon_id) == ctx.channel.id and str(ctx.author.id) == membre_id:
                est_autorise = True
                break

        if not est_autorise:
            await ctx.send("Tu n'as pas la permission de fermer ce ticket.")
            return

        for membre_id, salon_id in list(open_tickets.items()):
            if int(salon_id) == ctx.channel.id:
                close_ticket(str(ctx.guild.id), membre_id)
                break

        await ctx.send("Ticket fermé, salon supprimé dans 5 secondes.")
        await asyncio.sleep(5)
        await ctx.channel.delete()

    @commands.command(extras={"category": "Permissions & Logs"})
    async def close(self, ctx):
        perms_cog = self.bot.get_cog("Permissions")
        if not perms_cog or ctx.author.id not in perms_cog.owner_ids:
            await ctx.send("Tu n'as pas la permission.")
            return

        categories_tickets = [c for c in ctx.guild.categories if c.name.startswith("Tickets —")]
        if not categories_tickets:
            await ctx.send("Aucun ticket ouvert.")
            return

        total = sum(len(c.text_channels) for c in categories_tickets)
        if total == 0:
            await ctx.send("Aucun ticket ouvert.")
            return

        await ctx.send(f"Fermeture de {total} ticket(s) dans 5 secondes...")
        await asyncio.sleep(5)

        tickets_data = get_tickets(str(ctx.guild.id))
        open_tickets = tickets_data.get("open", {})

        for categorie_discord in categories_tickets:
            for salon in categorie_discord.text_channels:
                for membre_id, salon_id in list(open_tickets.items()):
                    if int(salon_id) == salon.id:
                        close_ticket(str(ctx.guild.id), membre_id)
                await salon.delete()
            await categorie_discord.delete()

        await ctx.send("Tous les tickets ont été fermés.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))