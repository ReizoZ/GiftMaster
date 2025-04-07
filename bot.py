import os
import asyncio
import logging
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands

from db_operations import init_db
from commands import create_giveaway, reroll, reroll_giveaway
from views import GiveawayView

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None 
)

@bot.event
async def on_ready():
    """Handler for when the bot is ready and connected to Discord."""
    logging.info(f"Logged in as {bot.user}")
    logging.info(f"Serving {len(bot.guilds)} guilds")
    
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Game("/giveaway")
    )
    
    await bot.tree.sync()
    # Ensure Database directory exists
    if not os.path.exists('./Database'):
        os.makedirs('./Database')
    
    # Initialize database
    await asyncio.to_thread(init_db)

from commands import create_giveaway, reroll, reroll_giveaway

async def giveaway_command(interaction: discord.Interaction, image: discord.Attachment = None):
    await create_giveaway(bot, interaction, image)

async def reroll_command(interaction: discord.Interaction, giveaway_id: str, number_of_winners: int = None):
    await reroll(bot, interaction, giveaway_id, number_of_winners)

async def reroll_giveaway_command(interaction: discord.Interaction, message: discord.Message):
    await reroll_giveaway(bot, interaction, message)

bot.tree.command(name="giveaway", description="Create a new giveaway")(giveaway_command)
bot.tree.command(name="reroll", description="Reroll a completed giveaway")(reroll_command)
bot.tree.context_menu(name="Reroll Giveaway")(reroll_giveaway_command)

async def main():
    """Main entry point to start the bot."""
    async with bot:
        await bot.start(TOKEN, reconnect=True)

if __name__ == "__main__":
    asyncio.run(main())
