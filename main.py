import sys
import logging
import discord
from discord.ext import commands

import config
from keep_alive import keep_alive

# Force unbuffered stdout so Render logs show immediately
sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bot")

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
INTENTS.voice_states = True
INTENTS.guilds = True

bot = commands.Bot(command_prefix="!", intents=INTENTS, help_command=None)

EXTENSIONS = [
    "cogs.tickets",
    "cogs.autorole",
    "cogs.logging_member",
    "cogs.logging_voice",
    "cogs.logging_messages",
    "cogs.logging_channels",
    "cogs.logging_roles",
    "cogs.moderation",
]


@bot.event
async def on_ready():
    logger.info(f"Συνδέθηκε ως {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Συγχρονίστηκαν {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Αποτυχία συγχρονισμού commands: {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="made by !3mma"))


async def main():
    async with bot:
        for ext in EXTENSIONS:
            try:
                await bot.load_extension(ext)
                logger.info(f"Φορτώθηκε extension: {ext}")
            except Exception as e:
                logger.error(f"Αποτυχία φόρτωσης {ext}: {e}")
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN δεν έχει οριστεί! Έλεγξε το .env ή τα Render environment variables.")
        sys.exit(1)

    keep_alive()

    import asyncio
    asyncio.run(main())
