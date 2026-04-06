import discord
from discord.ext import commands

class Suggestions(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Suggestions(bot))  

    import discord
from discord.ext import commands

SUGGESTION_CHANNEL = "suggestions"

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(extras={"category": "Suggestions"})
    async def suggestion(self, ctx, *, message: str = None):
        if not message:
            await ctx.send("Écris ta suggestion après la commande. Ex: `+suggestion mon idée`")
            return
        salon = discord.utils.get(ctx.guild.text_channels, name=SUGGESTION_CHANNEL)
        if not salon:
            await ctx.send("Salon `suggestions` introuvable. Crée-le d'abord.")
            return
        embed = discord.Embed(title="Nouvelle suggestion", description=message, color=0x00ff00)
        embed.set_footer(text=f"Par {ctx.author}", icon_url=ctx.author.display_avatar.url)
        msg = await salon.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        await ctx.message.delete()

    @commands.command(extras={"category": "Suggestions"})
    async def lb(self, ctx, categorie: str = "suggestions"):
        if categorie != "suggestions":
            await ctx.send("Catégorie inconnue.")
            return
        salon = discord.utils.get(ctx.guild.text_channels, name=SUGGESTION_CHANNEL)
        if not salon:
            await ctx.send("Salon suggestions introuvable.")
            return
        messages = []
        async for msg in salon.history(limit=50):
            for reaction in msg.reactions:
                if str(reaction.emoji) == "✅":
                    messages.append((msg, reaction.count))
        messages.sort(key=lambda x: x[1], reverse=True)
        if not messages:
            await ctx.send("Aucune suggestion trouvée.")
            return
        embed = discord.Embed(title="Top suggestions", color=0x00ff00)
        for i, (msg, count) in enumerate(messages[:5], 1):
            description = msg.embeds[0].description if msg.embeds else "?"
            embed.add_field(name=f"#{i} — {count} ✅", value=description, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))