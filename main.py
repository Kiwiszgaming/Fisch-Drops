import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create the bot with the desired prefix
bot = commands.Bot(command_prefix='!', intents=intents)

# Flask app for keeping the bot online
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run)
    thread.start()

# Dictionaries to store server configurations
server_config = {}
role_config = {}
command_roles = {}  # New: Store roles allowed to use commands for each server

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}!')

def has_permission(ctx):
    """Helper function to check if the user has the required role to use commands."""
    if ctx.guild.id not in command_roles:
        return True  # No restrictions set, allow all users
    role_id = command_roles[ctx.guild.id]
    role = discord.utils.get(ctx.guild.roles, id=role_id)
    if role in ctx.author.roles:
        return True
    return False

@bot.command()
async def config(ctx):
    """Command to configure the bot for the server."""
    if not has_permission(ctx):
        await ctx.send("You don't have permission to use this command.")
        return

    # Save the current channel ID for the server
    server_config[ctx.guild.id] = ctx.channel.id
    await ctx.send(f"Configured this channel for messages: {ctx.channel.mention}")

@bot.command()
async def setrole(ctx, role_id: int):
    """Command to set a custom ping role for this server."""
    if not has_permission(ctx):
        await ctx.send("You don't have permission to use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, id=role_id)
    if not role:
        await ctx.send("Invalid role ID provided. Please provide a valid role ID.")
        return

    # Save the role ID to the role configuration for the server
    role_config[ctx.guild.id] = role_id
    await ctx.send(f"Ping role set to {role.mention} for this server.")

@bot.command()
async def restrict(ctx, role_id: int):
    """Restrict who can use the bot's commands to members with a specific role."""
    if ctx.author.guild_permissions.administrator:  # Only admins can set restrictions
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        if not role:
            await ctx.send("Invalid role ID provided. Please provide a valid role ID.")
            return
        command_roles[ctx.guild.id] = role_id
        await ctx.send(f"Bot commands restricted to members with the role: {role.mention}")
    else:
        await ctx.send("You must be an administrator to restrict bot commands.")

@bot.command()
async def host(ctx, link: str = None, user: str = None):
    """Command to share private server details and broadcast to all configured channels."""
    if not has_permission(ctx):
        await ctx.send("You don't have permission to use this command.")
        return

    if not link or not user:
        await ctx.send("Usage: `!host <private server link> <hosted by>`")
        return

    if ctx.guild.id not in server_config:
        await ctx.send("Please configure the bot using `!config` first.")
        return

    # Create a visually appealing purple embed message
    embed = discord.Embed(
        title="🌌 Aurora Borealis Hosted!",
        description="Details for the newly hosted Aurora Borealis server.",
        color=discord.Color.purple()  # Purple color for the embed
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else 'https://via.placeholder.com/150')
    embed.add_field(name="Private Server Link", value=link, inline=False)
    embed.add_field(name="Hosted By", value=user, inline=False)
    embed.set_footer(text=f"Hosted by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else 'https://via.placeholder.com/32')

    # Send the embed to all configured channels
    for guild_id, channel_id in server_config.items():
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                # If a role ID is configured, mention the role in the message
                if guild_id in role_config:
                    role = discord.utils.get(channel.guild.roles, id=role_config[guild_id])
                    if role:
                        await channel.send(f"{role.mention} ", embed=embed)
                    else:
                        await channel.send(embed=embed)
                else:
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to send message to channel {channel_id} in guild {guild_id}: {e}")

    await ctx.send("Broadcast message sent to all configured servers.")

@bot.command()
async def ping(ctx):
    """Command to ping the configured role in the current server's configured channel."""
    if not has_permission(ctx):
        await ctx.send("You don't have permission to use this command.")
        return

    if ctx.guild.id not in role_config:
        await ctx.send("No role configured for this server. Use `!setrole` to set a role ID.")
        return

    role_id = role_config[ctx.guild.id]
    role = discord.utils.get(ctx.guild.roles, id=role_id)
    if not role:
        await ctx.send("Configured role not found. Please set a valid role ID using `!setrole`.")
        return

    if ctx.guild.id in server_config:
        channel_id = server_config[ctx.guild.id]
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(f"{role.mention} A new message for you!")
                await ctx.send(f"Pinging {role.mention} in the configured channel.")
            except Exception as e:
                print(f"Failed to send ping to channel {channel_id} in guild {ctx.guild.id}: {e}")
        else:
            await ctx.send("Configured channel not found. Please reconfigure using `!config`.")
    else:
        await ctx.send("Server not configured. Use `!config` to set up this server.")

# Keep the bot alive
keep_alive()

# Run the bot using the token from an environment variable
bot.run(os.getenv('DISCORD_BOT_TOKEN'))