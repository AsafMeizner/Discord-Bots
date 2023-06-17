import discord
from discord import app_commands
from dis_token import *

token = Thinker

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="gimmi", description="Assigns a role to the user or mentioned user")
async def gimmi(interaction, role_id: str, user: discord.Member = None):
    try:
        role_id = int(role_id)
    except ValueError:
        await interaction.response.send_message('Invalid role ID. Please provide a valid integer.', ephemeral=True)
        return

    role = interaction.guild.get_role(role_id)

    if role is None:
        await interaction.response.send_message('Error: Role not found.', ephemeral=True)
        return

    if user is None:
        try:
            member = await interaction.guild.fetch_member(interaction.user.id)
        except discord.NotFound:
            await interaction.response.send_message('Error: Member not found.', ephemeral=True)
            return
    else:
        member = user

    await member.add_roles(role)
    await interaction.response.send_message(f'Role {role.name} assigned to {member.name}.', ephemeral=True)

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/gimmi"))

client.run(token)