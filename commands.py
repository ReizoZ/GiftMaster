import discord
from discord.ext import commands
import random
from db_operations import get_giveaway_from_db
from modals import GiveawayModal

async def create_giveaway(bot: commands.Bot, interaction: discord.Interaction, image: discord.Attachment = None):
    """Slash command handler for creating a new giveaway."""
    if image is not None and not image.content_type.startswith('image'):
        await interaction.response.send_message(
            "Please provide a valid image attachment",
            ephemeral=True
        )
        return
        
    ctx = await bot.get_context(interaction)
    await interaction.response.send_modal(
        GiveawayModal(bot, ctx, str(ctx.author.mention), image)
    )

async def reroll(bot: commands.Bot, interaction: discord.Interaction, giveaway_id: str, number_of_winners: int = None):
    """Reroll a completed giveaway."""
    data = get_giveaway_from_db(giveaway_id)

    if data is None:
        await interaction.response.send_message("This message is not a completed giveaway message!", ephemeral=True)
        return
        
    creator_id = data.get("member", "")[2:-1]
    if str(interaction.user.id) != creator_id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You must be the giveaway creator or a server admin to reroll!",
            ephemeral=True
        )
        return
        
    if number_of_winners is None:
        number_of_winners = 1
        
    Entrants = data["Entrants"]
    entrants_ids = []
    for participant in Entrants:
        try:
            if isinstance(participant, dict):
                user_id = participant.get("id") or participant.get("user_id")
            else:
                user_id = participant
                
            if user_id:
                user_id = str(user_id).strip()
                if user_id.isdigit():
                    entrants_ids.append(user_id)
                    
        except Exception as e:
            print(f"Error processing participant: {e}")
            continue
            
    if not entrants_ids:
        await interaction.response.send_message(
            "Could not find valid participants. Please check the giveaway data.",
            ephemeral=True
        )
        return
        
    number_of_winners = min(int(number_of_winners), len(entrants_ids))
    winners = random.sample(entrants_ids, number_of_winners)
    winners_mentions = [f"<@{winner}>" for winner in winners if winner is not None]
    await interaction.response.send_message(
        f"🎊🎊 Congratulations  {' '.join(winners_mentions)} **You won the {data['Title']}** 🎊🎊")

    channel = bot.get_channel(interaction.channel.id)
    message = await channel.fetch_message(int(giveaway_id))
    for winner in winners:
        user_data = next((u for u in Entrants if isinstance(u, dict) and u.get("id") == winner), None)
        if user_data:
            user = await bot.fetch_user(winner)
            username = user_data.get("username", str(user))
        else:
            user = await bot.fetch_user(winner)
            username = str(user)
        embed = discord.Embed(title=" 🎊🎊 ** Congratulations ** 🎊🎊 ", color=user.color)
        embed.add_field(name=f"", value=f"  <@{winner}> ({username}) **You won the {data['Title']}**", inline=False)
        embed.add_field(name="", value=f"You can check it here : {message.jump_url}", inline=False)
        await user.send(embed=embed)

async def reroll_giveaway(bot: commands.Bot, interaction: discord.Interaction, message: discord.Message):
    """Context menu handler for rerolling giveaways (right-click on message)."""
    message_id = str(message.id)
    data = get_giveaway_from_db(message_id)
    
    if data is None:
        await interaction.response.send_message("This message is not a completed giveaway message!", ephemeral=True)
        return
        
    creator_id = data.get("member", "")[2:-1]
    if str(interaction.user.id) != creator_id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "You must be the giveaway creator or a server admin to reroll!",
            ephemeral=True
        )
        return
        
    number_of_winners = data["Winner"]
    Entrants = data["Entrants"]
    entrants_ids = []
    for participant in Entrants:
        try:
            if isinstance(participant, dict):
                user_id = participant.get("id") or participant.get("user_id")
            else:
                user_id = participant
                
            if user_id:
                user_id = str(user_id).strip()
                if user_id.isdigit():
                    entrants_ids.append(user_id)
                    
        except Exception as e:
            print(f"Error processing participant: {e}")
            continue
            
    if not entrants_ids:
        await interaction.response.send_message(
            "Could not find valid participants. Please check the giveaway data.",
            ephemeral=True
        )
        return
        
    number_of_winners = min(int(number_of_winners), len(entrants_ids))
    winners = random.sample(entrants_ids, number_of_winners)
    winners_mentions = [f"<@{winner}>" for winner in winners if winner is not None]
    await interaction.response.send_message(
        f"🎊🎊 Congratulations  {' '.join(winners_mentions)} **You won the {data['Title']}** 🎊🎊")
    for winner in winners:
        user_data = next((u for u in Entrants if isinstance(u, dict) and u.get("id") == winner), None)
        if user_data:
            user = await bot.fetch_user(winner)
            username = user_data.get("username", str(user))
        else:
            user = await bot.fetch_user(winner)
            username = str(user)
        embed = discord.Embed(title=" 🎊🎊 ** Congratulations ** 🎊🎊 ", color=user.color)
        embed.add_field(name=f"", value=f"  <@{winner}> ({username}) **You won the {data['Title']}**", inline=False)
        embed.add_field(name="", value=f"You can check it here : {message.jump_url}", inline=False)
        await user.send(embed=embed)
