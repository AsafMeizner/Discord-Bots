import discord
from discord import app_commands
import os
import random

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

truth_file = os.path.join(current_directory, "truth_or_dare", "truth_file.txt")
dare_file = os.path.join(current_directory, "truth_or_dare", "dare_file.txt")

truth_questions = load_questions(truth_file)
dare_questions = load_questions(dare_file)

class TruthOrDareView(discord.ui.View):
    def __init__(self, interaction):
        super().__init__(timeout=180.0)
        self.interaction = interaction
        self.question_type = None  # Store the current question type
        self.message = None  # To store the message object for editing

    async def send_initial_question(self, question_type):
        self.question_type = question_type
        question = self.get_random_question()
        embed = self.create_embed(question)
        self.message = await self.interaction.response.send_message(embed=embed, view=self)

    async def send_question(self, interaction):
        question = self.get_random_question()
        embed = self.create_embed(question)
        await interaction.response.defer()
        
        # Remove buttons from the previous message
        if self.message:
            await self.message.edit(view=None)
        
        # Send the new question with buttons
        self.message = await interaction.followup.send(embed=embed, view=self)

    def get_random_question(self):
        if self.question_type == "truth":
            return random.choice(truth_questions).strip()
        elif self.question_type == "dare":
            return random.choice(dare_questions).strip()

    def create_embed(self, question):
        Ecolor = discord.Color.green() if self.question_type == "truth" else discord.Color.red()
        embed = discord.Embed(
            title=f"Random {self.question_type.capitalize()}",
            description=question,
            color=Ecolor,
        )
        embed.set_author(
            name=f"Requested by {self.interaction.user.display_name}",
            icon_url=self.interaction.user.avatar.url,
        )
        return embed

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.green)
    async def on_truth(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.question_type = "truth"
        await self.send_question(interaction)

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.red)
    async def on_dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.question_type = "dare"
        await self.send_question(interaction)

    @discord.ui.button(label="Random", style=discord.ButtonStyle.blurple)
    async def on_random(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.question_type = random.choice(["truth", "dare"])
        await self.send_question(interaction)

@tree.command(name="truth", description="Gives you a random truth ☺️")
async def truth_from_console_command(interaction: discord.Interaction):
    view = TruthOrDareView(interaction)
    await view.send_initial_question("truth")

@tree.command(name="dare", description="Gives you a random dare 😈")
async def dare_from_console_command(interaction: discord.Interaction):
    view = TruthOrDareView(interaction)
    await view.send_initial_question("dare")

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/truth or /dare"))

client.run(token)
