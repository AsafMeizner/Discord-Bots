import discord
from discord import app_commands
from dis_token import *

token = Enigma

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="clone", description="Clones a user and sends a message as them")
async def clone_command(ctx, target_user: discord.Member, *, message_content: str):
    webhook = await ctx.channel.create_webhook(name=target_user.display_name)
    
    # Set a default avatar URL if the user doesn't have a valid avatar
    avatar_url = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
    
    await webhook.send(content=message_content, username=target_user.display_name, avatar_url=avatar_url)
    await webhook.delete()

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/clone"))

client.run(token)
