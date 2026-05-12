import discord
from discord.ext import commands
import asyncio
import time
from dotenv import load_dotenv
import os
load_dotenv()

# ======= PRÉFIXE =======

def load_prefix(bot, message):
    from database import get_prefix
    return get_prefix(str(message.guild.id) if message.guild else "+")

def save_prefix(guild_id: str, prefix: str):
    from database import set_prefix
    set_prefix(guild_id, prefix)

# ======= BOT =======

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=load_prefix, intents=intents)
bot.remove_command('help')
bot.start_time = None

# ======= EVENTS =======

@bot.event
async def on_ready():
    bot.start_time = time.time()
    await bot.change_presence(
        activity=discord.Streaming(name="armin.bot", url="https://twitch.tv/lei_bad")
    )
    print(f"Bot connecté en tant que {bot.user} — prêt !")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Tu n'as pas les permissions pour faire ça.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Membre introuvable.")
    elif isinstance(error, commands.CommandNotFound):
        pass

# ======= HELP =======
class HelpSelect(discord.ui.Select):
    def __init__(self, categories):
        self.categories_data = categories
        icones = {
            "Musique": "🎵",
            "Utilitaires": "🔧",
            "Modération": "🔨",
            "Suggestions": "💡",
            "Permissions & Logs": "⚙️",
            "Autres": "📌"
        }
        options = [
            discord.SelectOption(
                label=cat,
                emoji=icones.get(cat, "📌")
            )
            for cat in categories
        ]
        super().__init__(placeholder="Choisis une catégorie...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        icones = {
            "Musique": "🎵",
            "Utilitaires": "🔧",
            "Modération": "🔨",
            "Suggestions": "💡",
            "Permissions & Logs": "⚙️",
            "Autres": "📌"
        }
        embed = discord.Embed(
            title=f"{icones.get(cat, '📌')} {cat}",
            description="\n".join(self.categories_data[cat]),
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class HelpView(discord.ui.View):
    def __init__(self, categories):
        super().__init__(timeout=None)
        self.add_item(HelpSelect(categories))

@bot.command(name="help")
async def help_cmd(ctx):
    categories = {}
    ordre = ["Musique", "Utilitaires", "Suggestions", "Modération", "Permissions & Logs", "Autres"]
    for cmd in sorted(bot.commands, key=lambda c: c.name):
        cat = cmd.extras.get("category", "Autres")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f"`+{cmd.name}`")
    categories_ordonnees = {cat: categories[cat] for cat in ordre if cat in categories}
    embed = discord.Embed(
        title="Commandes du bot",
        description="Sélectionne une catégorie pour voir les commandes disponibles.",
        color=0x00ff00
    )
    icones = {
        "Musique": "🎵",
        "Utilitaires": "🔧",
        "Modération": "🔨",
        "Suggestions": "💡",
        "Permissions & Logs": "⚙️",
        "Autres": "📌"
    }
    for cat in ordre:
        if cat in categories:
            embed.add_field(
                name=f"{icones.get(cat, '📌')} {cat}",
                value=f"{len(categories[cat])} commandes",
                inline=True
            )
    await ctx.send(embed=embed, view=HelpView(categories_ordonnees))

# ======= LANCEMENT =======

TOKEN = os.getenv("TOKEN")

async def main():
    async with bot:
        await bot.load_extension("cogs.logs")
        await bot.load_extension("cogs.permissions")
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.utilitaires")
        await bot.load_extension("cogs.suggestions")
        await bot.load_extension("cogs.musique")
        await bot.load_extension("cogs.tickets")
        await bot.start(TOKEN)

asyncio.run(main())



