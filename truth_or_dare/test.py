import discord
from discord import app_commands

import os
import random
import string

current_directory = os.getcwd()

from dis_token import TOD
token = TOD

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Load truth and dare questions from files
def load_questions(file_path):
    with open(file_path, "r") as file:
        questions = file.readlines()
    return questions

truth_file = current_directory + "\\truth_or_dare\\truth_file.txt"
dare_file = current_directory + "\\truth_or_dare\\dare_file.txt"

truth_questions = load_questions(truth_file)
dare_questions = load_questions(dare_file)

# Store the user responses for the Rice Purity Test
user_responses = {}

class TruthOrDareView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = None

    async def send_question(self, question_type):
        if question_type == "truth":
            question = random.choice(truth_questions).strip()
        else:
            question = random.choice(dare_questions).strip()

        embed = discord.Embed(title=f"Random {question_type.capitalize()}", description=question, color=discord.Color.blurple())
        embed.set_author(name="Requested by user", icon_url=self.interaction.user.avatar.url)

        if self.message is None:
            self.message = await self.interaction.response.send_message(embed=embed, view=self)
        else:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.green)
    async def on_truth(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.send_question("truth")

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.red)
    async def on_dare(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.send_question("dare")

    @discord.ui.button(label="Random", style=discord.ButtonStyle.blurple)
    async def on_random(self, button: discord.ui.Button, interaction: discord.Interaction):
        question_type = random.choice(["truth", "dare"])
        await self.send_question(question_type)

@tree.command(name="truth", description="Gives you a random truth ☺️")
async def truth_from_console_command(interaction):
    view = TruthOrDareView()
    await view.send_question("truth")

@tree.command(name="dare", description="Gives you a random dare 😈")
async def dare_from_console_command(interaction):
    view = TruthOrDareView()
    await view.send_question("dare")

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/truth or /dare"))

client.run(token)
