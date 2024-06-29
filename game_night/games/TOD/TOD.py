import discord
from discord import app_commands
import os
import random
from main import truth_questions, dare_questions

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