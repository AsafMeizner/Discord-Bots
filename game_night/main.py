import discord
from discord import app_commands

from dis_token import GAMENIGHT
token = GAMENIGHT

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

from ini import *
truth_questions = get_truth()
dare_questions = get_dare()
rice_purity_questions = get_RICE()

# from games.RICE.rice_purity import *



# ===========================================================================

from games.TOD.TOD import *

@tree.command(name="truth", description="Gives you a random truth ☺️")
async def truth_from_console_command(interaction: discord.Interaction):
    view = TruthOrDareView(interaction)
    await view.send_initial_question("truth")

@tree.command(name="dare", description="Gives you a random dare 😈")
async def dare_from_console_command(interaction: discord.Interaction):
    view = TruthOrDareView(interaction)
    await view.send_initial_question("dare")

# ===========================================================================

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/help"))

client.run(token)