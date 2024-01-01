import discord
from discord import app_commands
from dis_token import TOD

token = TOD

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

@tree.command(name="clone", description="Clones a user and sends a message as them")
async def clone_command(ctx, target_user: discord.Member, *, message_content: str):
    webhook = await ctx.channel.create_webhook(name=target_user.display_name)

    avatar_url = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
    
    await webhook.send(content=message_content, username=target_user.display_name, avatar_url=avatar_url)
    await webhook.delete()

@tree.command(name="server_mute", description="server mutes a selected user")
async def server_mute_command(interaction, target_user: discord.Member):
    await target_user.edit(mute=True)
    await interaction.response.send_message(f"{target_user.mention} has been server muted.", ephemeral=True)

@tree.command(name="server_unmute", description="server unmutes a selected user")
async def server_unmute_command(interaction, target_user: discord.Member):
    await target_user.edit(mute=False)
    await interaction.response.send_message(f"{target_user.mention} has been server unmuted.", ephemeral=True)

@tree.command(name="server_deafen", description="server deafens a selected user")
async def server_deafen_command(interaction, target_user: discord.Member):
    await target_user.edit(deafen=True)
    await interaction.response.send_message(f"{target_user.mention} has been server deafened.", ephemeral=True)

@tree.command(name="server_undeafen", description="server undeafens a selected user")
async def server_undeafen_command(interaction, target_user: discord.Member):
    await target_user.edit(deafen=False)
    await interaction.response.send_message(f"{target_user.mention} has been server undeafened.", ephemeral=True)

@tree.command(name="disconnect_voice", description="disconnects a selected user")
async def disconnect_voice_command(interaction, target_user: discord.Member):
    await target_user.edit(voice_channel=None)
    await interaction.response.send_message(f"{target_user.mention} has been disconnected.", ephemeral=True)

@tree.command(name="move_voice", description="moves a selected user to a selected voice channel")
async def move_voice_command(interaction, target_user: discord.Member, target_channel: discord.VoiceChannel):
    await target_user.edit(voice_channel=target_channel)
    await interaction.response.send_message(f"{target_user.mention} has been moved to {target_channel.mention}.", ephemeral=True)

@tree.command(name="change_nickname", description="change server nickname of a selected user")
async def change_server_nickname_command(interaction, target_user: discord.Member, new_nickname: str):
    await target_user.edit(nick=new_nickname)
    await interaction.response.send_message(f"{target_user.mention}'s nickname has been changed to {new_nickname}.", ephemeral=True)

# @tree.command(name="delete_message", description="deletes a selected message")
# async def delete_message_command(interaction, target_message: discord.Message):
#     await target_message.delete()
#     await interaction.response.send_message(f"Message deleted.", ephemeral=True)

@tree.command(name="print_all_bot_premitions", description="prints a list of all the thing the bot can do")
async def print_all_bot_premitions_command(interaction):
    await interaction.response.send_message(f"Bot premitions: {interaction.guild.me.guild_permissions}", ephemeral=True)
    print(interaction.guild.me.guild_permissions)
    

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/clone"))

client.run(token)