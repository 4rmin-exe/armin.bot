import discord
from discord.ext import commands
import asyncio
import time
from dotenv import load_dotenv
import os
from server import keep_alive
load_dotenv(r"C:\Users\Daniel\Desktop\Danny\armin.bot\.env")

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

@bot.command(name="help")
async def help_cmd(ctx):
    categories = {}
    for cmd in sorted(bot.commands, key=lambda c: c.name):
        cat = cmd.extras.get("category", "Autres")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f"`+{cmd.name}`")

    icones = {
        "Musique": "🎵",
        "Utilitaires": "🔧",
        "Modération": "🔨",
        "Suggestions": "💡",
        "Permissions & Logs": "⚙️",
        "Autres": "📌"
    }

    ordre = ["Musique", "Utilitaires", "Suggestions", "Modération", "Permissions & Logs", "Autres"]
    embed = discord.Embed(title="Commandes du bot", color=0x00ff00)
    for cat in ordre:
        if cat in categories:
            icone = icones.get(cat, "📌")
            embed.add_field(name=f"{icone} {cat}", value=", ".join(categories[cat]), inline=False)
    await ctx.send(embed=embed)

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

keep_alive()
asyncio.run(main())