import discord
from discord.ext import commands
from database import get_owners, add_owner, remove_owner

OWNER_ID = 760550316008538182

class Permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_ids = {OWNER_ID}
        self.custom_perms = {}

    async def cog_load(self):
        pass

    def is_owner(self, user_id):
        return user_id in self.owner_ids

    @commands.command(extras={"category": "Permissions & Logs"})
    async def owner(self, ctx, membre: discord.Member = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not membre:
            await ctx.send("Mentionne un membre.")
            return
        self.owner_ids.add(membre.id)
        add_owner(str(ctx.guild.id), membre.id)
        await ctx.send(f"{membre.mention} a été ajouté comme owner.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def removeowner(self, ctx, membre: discord.Member = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not membre:
            await ctx.send("Mentionne un membre.")
            return
        if membre.id == OWNER_ID:
            await ctx.send("Tu ne peux pas retirer le owner principal.")
            return
        self.owner_ids.discard(membre.id)
        remove_owner(str(ctx.guild.id), membre.id)
        await ctx.send(f"{membre.mention} a été retiré des owners.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def ownerlist(self, ctx):
        if not self.owner_ids:
            await ctx.send("Aucun owner enregistré.")
            return
        embed = discord.Embed(title="Liste des owners", color=0x00ff00)
        owners = []
        for id in self.owner_ids:
            user = await self.bot.fetch_user(id)
            owners.append(user.mention)
        embed.description = "\n".join(owners)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Permissions & Logs"})
    async def newperm(self, ctx, nom: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom:
            await ctx.send("Donne un nom. Ex: `+newperm perm1`")
            return
        if nom in self.custom_perms:
            await ctx.send(f"La permission `{nom}` existe déjà.")
            return
        self.custom_perms[nom] = {"roles": [], "commands": []}
        await ctx.send(f"Permission `{nom}` créée.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def delperm(self, ctx, nom: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom or nom not in self.custom_perms:
            await ctx.send("Permission introuvable.")
            return
        del self.custom_perms[nom]
        await ctx.send(f"Permission `{nom}` supprimée.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def setperm(self, ctx, nom: str = None, cible: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom or not cible:
            await ctx.send("Utilise `+setperm <perm> <@role/everyone>`")
            return
        if nom not in self.custom_perms:
            await ctx.send(f"Permission `{nom}` introuvable. Crée-la avec `+newperm`.")
            return
        if cible.lower() == "everyone":
            if "everyone" not in self.custom_perms[nom]["roles"]:
                self.custom_perms[nom]["roles"].append("everyone")
            await ctx.send(f"Permission `{nom}` accordée à tout le monde.")
            return
        if ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id not in self.custom_perms[nom]["roles"]:
                self.custom_perms[nom]["roles"].append(role.id)
            await ctx.send(f"Permission `{nom}` accordée à {role.mention}.")
        else:
            await ctx.send("Mentionne un rôle ou écris `everyone`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def unsetperm(self, ctx, nom: str = None, cible: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom or not cible:
            await ctx.send("Utilise `+unsetperm <perm> <@role/everyone>`")
            return
        if nom not in self.custom_perms:
            await ctx.send(f"Permission `{nom}` introuvable.")
            return
        if cible.lower() == "everyone":
            if "everyone" in self.custom_perms[nom]["roles"]:
                self.custom_perms[nom]["roles"].remove("everyone")
            await ctx.send(f"Permission `everyone` retirée de `{nom}`.")
            return
        if ctx.message.role_mentions:
            role = ctx.message.role_mentions[0]
            if role.id in self.custom_perms[nom]["roles"]:
                self.custom_perms[nom]["roles"].remove(role.id)
            await ctx.send(f"Rôle {role.mention} retiré de `{nom}`.")
        else:
            await ctx.send("Mentionne un rôle ou écris `everyone`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def switch(self, ctx, nom: str = None, cmd: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom or not cmd:
            await ctx.send("Utilise `+switch <perm> <commande>`")
            return
        if nom not in self.custom_perms:
            await ctx.send(f"Permission `{nom}` introuvable.")
            return
        for perm in self.custom_perms.values():
            if cmd in perm["commands"]:
                perm["commands"].remove(cmd)
        self.custom_perms[nom]["commands"].append(cmd)
        await ctx.send(f"Commande `+{cmd}` déplacée vers `{nom}`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def duperm(self, ctx, nom: str = None, cmd: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not nom or not cmd:
            await ctx.send("Utilise `+duperm <perm> <commande>`")
            return
        if nom not in self.custom_perms:
            await ctx.send(f"Permission `{nom}` introuvable.")
            return
        if cmd not in self.custom_perms[nom]["commands"]:
            self.custom_perms[nom]["commands"].append(cmd)
        await ctx.send(f"Commande `+{cmd}` ajoutée à `{nom}`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def switchall(self, ctx, source: str = None, dest: str = None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not source or not dest:
            await ctx.send("Utilise `+switchall <perm_source> <perm_dest>`")
            return
        if source not in self.custom_perms or dest not in self.custom_perms:
            await ctx.send("Une des permissions est introuvable.")
            return
        cmds = self.custom_perms[source]["commands"].copy()
        self.custom_perms[dest]["commands"].extend(cmds)
        self.custom_perms[source]["commands"] = []
        await ctx.send(f"Toutes les commandes de `{source}` déplacées vers `{dest}`.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def perms(self, ctx):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not self.custom_perms:
            await ctx.send("Aucune permission configurée.")
            return
        embed = discord.Embed(title="Permissions et commandes", color=0x00ff00)
        for nom, data in self.custom_perms.items():
            cmds = ", ".join([f"`+{c}`" for c in data["commands"]]) or "Aucune"
            embed.add_field(name=nom, value=cmds, inline=False)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Permissions & Logs"})
    async def confperms(self, ctx):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        if not self.custom_perms:
            await ctx.send("Aucune permission configurée.")
            return
        embed = discord.Embed(title="Configuration des permissions", color=0x00ff00)
        for nom, data in self.custom_perms.items():
            roles = []
            for r in data["roles"]:
                if r == "everyone":
                    roles.append("@everyone")
                else:
                    role = ctx.guild.get_role(r)
                    roles.append(role.mention if role else str(r))
            roles_str = ", ".join(roles) or "Aucun rôle"
            embed.add_field(name=nom, value=roles_str, inline=False)
        await ctx.send(embed=embed)

    @commands.command(extras={"category": "Permissions & Logs"})
    async def renewperms(self, ctx):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        self.custom_perms.clear()
        await ctx.send("Permissions réinitialisées.")

    @commands.command(extras={"category": "Permissions & Logs"})
    async def resetperms(self, ctx):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Tu n'as pas la permission.")
            return
        for perm in self.custom_perms.values():
            perm["roles"] = []
        await ctx.send("Toutes les permissions ont été désactivées sauf owner.")

async def setup(bot):
    await bot.add_cog(Permissions(bot))