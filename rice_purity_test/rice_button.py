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

# Load Rice Purity Test questions from a file
def load_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        questions = file.readlines()
    return questions

rice_purity_file = current_directory + "\\rice_purity_test\\rice_purity_questions.txt"
rice_purity_questions = load_questions(rice_purity_file)

# Store the user responses for the Rice Purity Test
user_responses = {}

class RicePurityView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180.0)
        self.interaction = interaction
        self.current_question = 0
        self.score = 100
        self.anonymous = False  # Default to non-anonymous mode

    async def send_question(self):
        question = rice_purity_questions[self.current_question].strip()
        await self.message.edit(content=question, view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def on_yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.process_response("yes")

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def on_no(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.process_response("no")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.grey)
    async def on_stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Rice Purity Test stopped.", ephemeral=True)

    async def process_response(self, answer: str):
        user_responses[self.current_question] = answer
        self.current_question += 1
        if answer == "yes":
            self.score -= 1

        if self.current_question < len(rice_purity_questions):
            await self.send_question()
        else:
            user_mention = self.interaction.user.mention if not self.anonymous else "Anonymous User"
            score_message = f"{user_mention}'s rice purity score is: {self.score} 😈"
            await self.interaction.followup.send(score_message, ephemeral=self.anonymous)

@tree.command(name="ricepurity", description="Take the Rice Purity Test! Respond with buttons 'Yes' or 'No'. Type '!stop' to end the test.")
async def rice_purity_test_command(interaction, anonymous: str = "false"):
    await interaction.response.send_message("Starting Rice Purity Test...", ephemeral=True)

    anonymous = anonymous.lower().strip()

    if anonymous not in ["true", "false", "yes", "no"]:
        await interaction.followup.send("Invalid value for the 'anonymous' field. Please use 'true' or 'false'.", ephemeral=True)
        return

    anonymous = anonymous in ["true", "yes"]

    view = RicePurityView(interaction)
    view.anonymous = anonymous
    view.message = await interaction.followup.send("Loading question...", ephemeral=True, view=view)
    await view.send_question()

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/ricepurity"))

client.run(token)