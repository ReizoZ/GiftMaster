import discord
from discord import Interaction
from discord.ui import Item, View, Button
from discord.ext import commands
from typing import Any
import asyncio
import logging
import random
import time as time_module
import datetime
from db_operations import save_giveaway_to_db
import os

class ExitView(discord.ui.View):
    """View containing a button to cancel a giveaway."""
    
    def __init__(self):
        super().__init__()
        self.value = None
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_giveaway(self, interaction: discord.Interaction, button: discord.Button):
        """Handle giveaway cancellation."""
        await interaction.response.edit_message(
            content="You have successfully canceled the giveaway ✅",
            view=None
        )
        self.value = True
        self.stop()

class LeaveGiveawayView(discord.ui.View):
    """View allowing users to leave a giveaway."""
    
    def __init__(self, timeout=False):
        super().__init__(timeout=timeout)
        self.user_responses = {}  
        self.timeout_trackers = {}  
    
    @discord.ui.button(label="Leave Giveaway", style=discord.ButtonStyle.red)
    async def leave_giveaway(self, interaction: discord.Interaction, button: discord.Button):
        """Handle user leaving a giveaway."""
        user_id = interaction.user.id
        
        if user_id in self.timeout_trackers:
            self.user_responses[str(user_id)] = 1
            await interaction.response.edit_message(
                content="You have successfully left the giveaway! ✅",
                view=None
            )
        else:
            await interaction.response.edit_message(
                content="Timed out. Please try again ❌",
                view=None
            )
    
    async def wait_for_response(self, user_id: int) -> bool:
        """
        Wait for user response with timeout.
        
        Args:
            user_id: The Discord user ID to wait for
            
        Returns:
            bool: True if user left, False if timed out
        """
        if user_id in self.timeout_trackers:
            self.timeout_trackers[user_id] = 299
            return
        
        self.timeout_trackers[user_id] = 299

        while True:
            if self.user_responses.get(str(user_id)) == 1:
                del self.timeout_trackers[user_id]
                return True
                
            if self.timeout_trackers[user_id] == 0:
                del self.timeout_trackers[user_id]
                return False
                
            self.timeout_trackers[user_id] -= 1
            await asyncio.sleep(1)

    async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any]) -> None:
        """Handle errors in the view."""
        logging.error(f"Error in LeaveGiveawayView: {error}")

class GiveawayView(discord.ui.View):
    """View for managing a giveaway including entry, countdown and winner selection."""
    
    def __init__(self, bot: commands.Bot, ctx: commands.Context, timeout=False):
        """
        Initialize a new giveaway view.
        
        Args:
            bot: The bot instance
            ctx: The command context
            timeout: Whether the view should timeout automatically
        """
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.duration_seconds = None  
        self.is_active = None  
        self.participants = []  
        self.entry_count = 0  
        self.countdown_task = None  
        self.winners = []  
        self.end_timestamp = None  
        self.giveaway_message = None  
        self.giveaway_data = {}  
        self.title = None  
        self.winner_count = None  
        self.duration_string = None  
        self.description = None  
        self.host_mention = None  
        self.image_url = None  
        self.leave_view = LeaveGiveawayView()  

    def setup_giveaway(self, host: str, title: str, winner_count: str, 
                     duration_str: str, description: str, image_url: str) -> None:
        """
        Configure giveaway details.
        
        Args:
            host: Host member mention string
            title: Prize title
            winner_count: Number of winners as string
            duration_str: Duration string (e.g. "10 minutes")
            description: Giveaway description
            image_url: Optional image URL
        """
        self.host_mention = host
        self.title = title
        self.winner_count = winner_count
        self.duration_string = duration_str
        self.description = description 
        self.image_url = image_url
        
        now = datetime.datetime.now()
        self.creation_time = now.strftime('%A %d %b %Y %I:%M %p')

    def parse_duration(self) -> bool:
        """
        Parse duration string into seconds and set end timestamp.
        
        Returns:
            bool: True if parsing succeeded, False otherwise
        """
        duration_str = self.duration_string.lower()
        duration_parts = duration_str.split()
        
        if not duration_parts or not duration_parts[0].isdigit():
            return False
            
        duration = int(duration_parts[0])
        
        if duration_str.endswith(("sec", "second", "seconds")):
            self.duration_seconds = duration
        elif duration_str.endswith(("mn", "min", "minute", "minutes")):
            self.duration_seconds = duration * 60
        elif duration_str.endswith(("h", "hour", "hours")):
            self.duration_seconds = duration * 3600 
        elif duration_str.endswith(("d", "day", "days")):
            self.duration_seconds = duration * 86400
        else:
            return False
            
        self.end_timestamp = time_module.time() + self.duration_seconds
        return True

    def create_embed(self) -> discord.Embed:
        """Create the giveaway embed with current information."""
        try:
            avatar = self.ctx.author.avatar.url
        except AttributeError:
            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
            
        embed = discord.Embed(
            title=f"**{self.title}**",
            description=f"{self.description or ''}",
            color=discord.Color.blurple() 
        )  
        if not self.image_url:
             embed.set_thumbnail(url=avatar)
        
        embed.add_field(
            name="⏰ Ends", 
            value=f"<t:{int(self.end_timestamp)}:R> (<t:{int(self.end_timestamp)}:f>)", 
            inline=False
        )
        embed.add_field(name="👑 Hosted by", value=self.host_mention, inline=True) 
        embed.add_field(name="👥 Entries", value=self.entry_count, inline=True) 
        embed.add_field(name="🏆 Winners", value=self.winner_count, inline=True) 
        embed.set_footer(text=f"Giveaway started", icon_url=avatar)
        embed.timestamp = datetime.datetime.fromtimestamp(time_module.time()) 

        if self.image_url:
            embed.set_image(url=self.image_url)
            
        return embed

    async def update_giveaway_message(self, channel: discord.TextChannel):
        """Update the giveaway message with current participant count."""
        try:
            msg = await channel.fetch_message(self.giveaway_message.id)
            await msg.edit(embed=self.create_embed())
        except Exception as e:
            logging.error(f"Error updating giveaway message: {e}")

    @discord.ui.button(label="", style=discord.ButtonStyle.blurple, emoji="🎉")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.Button):
        """Handle user entering the giveaway."""
        user_id = interaction.user.id
        
        if user_id in self.participants:
            self.leave_view.user_responses[str(user_id)] = 0
            await interaction.response.send_message(
                content="You have already entered this giveaway!",
                ephemeral=True, 
                view=self.leave_view
            )
            
            did_leave = await self.leave_view.wait_for_response(user_id)
            if did_leave and user_id in self.participants:
                self.entry_count -= 1
                self.participants.remove(user_id)
                await self.update_giveaway_message(interaction.channel)
            return
                
        self.participants.append(user_id)
        self.entry_count += 1
        await interaction.response.edit_message(embed=self.create_embed())

    async def run_countdown(self):
        """Run the giveaway countdown and select winners when time expires."""
        self.countdown_task = asyncio.create_task(asyncio.sleep(self.duration_seconds))
        await self.countdown_task
        
        try:
            channel = self.bot.get_channel(self.giveaway_message.channel.id)
            await channel.fetch_message(self.giveaway_message.id)
        except discord.NotFound:
            logging.error("Giveaway message was deleted")
            self.is_active = False
            self.stop()
            self.leave_view.stop()
            return
            
        if self.entry_count == 0:
            await self.giveaway_message.channel.send(
                f"{self.host_mention} No one entered your giveaway"
            )
            await self.end_giveaway()
            return
            
        winner_count = min(int(self.winner_count), self.entry_count)
        winner_ids = random.sample(self.participants, winner_count)
        self.winners = [f"<@{winner_id}>" for winner_id in winner_ids]
        
        self.save_giveaway_data()
        await self.announce_winners(winner_ids)
        await self.update_ended_giveaway()
        await self.send_host_summary()
        
        self.is_active = False
        self.stop()
        self.leave_view.stop()

    async def end_giveaway(self):
        """Clean up when giveaway ends with no participants."""
        channel = self.bot.get_channel(self.giveaway_message.channel.id)
        msg = await channel.fetch_message(self.giveaway_message.id)
        
        self.clear_items()
        await msg.edit(embed=self.create_embed(), view=self)
        
        self.is_active = False
        self.stop()
        self.leave_view.stop()

    def save_giveaway_data(self):
        """Save giveaway data to database."""
        entrants_data = []
        for user_id in self.participants:
            user = self.bot.get_user(user_id)
            if user:
                entrants_data.append({
                    "id": str(user.id),
                    "username": user.name,
                    "display_name": user.display_name,
                    "discriminator": user.discriminator,
                    "avatar": str(user.avatar.url) if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                    "created_at": str(user.created_at),
                    "joined_at": str(user.joined_at) if hasattr(user, 'joined_at') else None
                })
            else:
                entrants_data.append(str(user_id))  
        
        giveaway_data = {
            "member": self.host_mention,
            "Title": self.title,
            "Winner": self.winner_count,
            "Time": self.duration_seconds,
            "Description": self.description,
            "Entries": self.entry_count,
            "Entrants": entrants_data,
            "Winners": self.winners
        }
        
        save_giveaway_to_db(str(self.giveaway_message.id), giveaway_data)

    async def announce_winners(self, winner_ids: list[int]):
        """Announce winners in channel and DM them.
        
        Args:
            winner_ids: List of winner user IDs
        """
        await self.giveaway_message.channel.send(
            f"🎊🎊 Congratulations {' '.join(self.winners)} "
            f"**You won the {self.title}** 🎊🎊"
        )
        
        for winner_id in winner_ids:
            user = await self.bot.fetch_user(winner_id)
            embed = discord.Embed(
                title="🏆 Congratulations! You Won! 🏆",
                description=f"Hey {user.mention}, you won the **{self.title}** giveaway!",
                color=discord.Color.gold() 
            )
            embed.add_field(
                name="🎁 Prize", 
                value=self.title,
                inline=False
            )
            embed.add_field(
                name="🔗 Giveaway Link",
                value=f"[Click Here]({self.giveaway_message.jump_url})",
                inline=False
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/715914936945147914.gif?v=1") 
            embed.set_footer(text=f"Hosted by {self.ctx.author.display_name}", icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None)
            embed.timestamp = datetime.datetime.now()
            await user.send(embed=embed)

    async def update_ended_giveaway(self):
        """Update the giveaway message after it ends."""
        self.winner_count = " ".join(self.winners)
        self.clear_items()
        
        channel = self.bot.get_channel(self.giveaway_message.channel.id)
        msg = await channel.fetch_message(self.giveaway_message.id)
        embed = self.create_embed()
        summary_button = Button(
            label="Giveaway Summary",
            style=discord.ButtonStyle.link,
            url=f"{os.getenv('DOMAIN')}/{self.giveaway_message.id}"
        )
        self.add_item(summary_button)
             
        await msg.edit(embed=embed, view=self)

    async def send_host_summary(self):
        """Send a summary DM to the giveaway host."""
        channel = await self.ctx.author.create_dm()
        entrants = [f"<@{user_id}>" for user_id in self.participants]
        entrants_str = ' '.join(entrants)
        
        
        summary_embed = discord.Embed(
            title="📊 Giveaway Summary 📊",
            description=f"Here's the summary for your giveaway: **{self.title}**",
            color=discord.Color.green() 
        )
        summary_embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        summary_embed.add_field(name="🎁 Prize", value=self.title, inline=False)
        summary_embed.add_field(name="🏆 Winners", value=' '.join(self.winners) if self.winners else "None", inline=False)
        
        
        if len(entrants_str) > 1000:
             entrants_display = f"{len(self.participants)} entrants (list too long to display)"
        elif not entrants_str:
             entrants_display = "No entrants"
        else:
             entrants_display = entrants_str
             
        summary_embed.add_field(name="👥 Entrants", value=entrants_display, inline=False)
        summary_embed.add_field(name="🆔 Giveaway ID", value=str(self.giveaway_message.id), inline=False)
        summary_embed.add_field(name="🔗 Giveaway Link", value=f"[Click Here]({self.giveaway_message.jump_url})", inline=False)

        summary_embed.set_footer(text=f"Giveaway ended", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        summary_embed.timestamp = datetime.datetime.now()

        await channel.send(embed=summary_embed)

    async def stop_giveaway(self):
        """Stop the giveaway and clean up resources."""
        self.is_active = False
        
        if self.countdown_task and not self.countdown_task.done():
            self.countdown_task.cancel()
            
        self.leave_view.stop()
        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: Item[Any]) -> None:
        """Handle errors in the giveaway view."""
        logging.error(f"Error in GiveawayView: {error}")
