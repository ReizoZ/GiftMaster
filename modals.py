import asyncio
import discord
from discord.ui import Modal, TextInput
from discord.ext import commands
from typing import Any
import logging
from views import GiveawayView, ExitView

class GiveawayModal(discord.ui.Modal, title="Create a Giveaway"):
    Title = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Prize",
        placeholder=" EX: 1000 dollar "
    )
    Winner = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="The number of winners",
        default="1",
    )
    Time = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Time",
        placeholder=" EX: 10 minutes,  10 hours,  10 days. "
    )
    Link = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Photo Links",
        placeholder=" The source URL for the image. Only HTTP(S) is supported. Inline attachment URLs are also supported ",
        required=False
    )
    description = discord.ui.TextInput(
        style=discord.TextStyle.long,
        required=False,
        label="Description",
        max_length=300,
    )

    def __init__(self, bot: commands.Bot, ctx: commands.Context, host_mention: str, image: discord.Attachment = None, timeout=None):
        """
        Initialize the giveaway creation modal.
        
        Args:
            bot: The bot instance
            ctx: Command context
            host_mention: Mention string of the host member
            image: Optional image attachment
            timeout: Modal timeout
        """
        self.image = image
        self.host_mention = host_mention
        self.ctx = ctx
        self.bot = bot
        self.giveaway_view = GiveawayView(self.bot, self.ctx)
        self.exit_view = ExitView()
        super().__init__(timeout=timeout)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission and create the giveaway."""
        # Validate image URL if provided
        image_url = self.image.url if self.image is not None else str(self.Link)
        if image_url and not image_url.startswith("https"):
            await interaction.response.send_message(
                "Image URL must use HTTPS protocol",
                ephemeral=True
            )
            return
            
        # Validate winner count
        if not self.Winner.value.isnumeric():
            await interaction.response.send_message(
                "Please enter a valid number of winners",
                ephemeral=True
            )
            return
            
        # Setup the giveaway view
        self.giveaway_view.setup_giveaway(
            host=self.host_mention,
            title=str(self.Title),
            winner_count=str(self.Winner),
            duration_str=str(self.Time),
            description=str(self.description),
            image_url=image_url
        )
        
        # Validate and parse duration
        if not self.giveaway_view.parse_duration():
            await interaction.response.send_message(
                "Please enter a valid duration (e.g. '10 minutes')",
                ephemeral=True
            )
            return
            
        # Create the giveaway message
        embed = self.giveaway_view.create_embed()
        await interaction.response.send_message(embed=embed, view=self.giveaway_view)
        
        # Get the message reference
        message = await interaction.original_response()
        self.giveaway_view.giveaway_message = message
        
        # Setup exit view
        self.exit_view.timeout = self.giveaway_view.duration_seconds
        await interaction.followup.send(
            f"Giveaway created successfully! ID: {message.id}",
            ephemeral=True,
            view=self.exit_view
        )
        
        # Start countdown
        countdown_task = asyncio.create_task(self.giveaway_view.run_countdown())
        
        # Handle cancellation
        await self.exit_view.wait()
        if self.exit_view.value:  # User cancelled
            if interaction.user.id == self.ctx.author.id:
                await message.delete()
                await self.giveaway_view.stop_giveaway()
                
        await countdown_task

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors."""
        logging.error(f"Error in GiveawayModal: {error}")
        await interaction.response.send_message(
            "An error occurred while creating the giveaway",
            ephemeral=True
        )
