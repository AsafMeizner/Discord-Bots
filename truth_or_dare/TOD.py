import discord
from discord import app_commands
from dis_token import *

import random
from dis_token import TOD 
from dis_token import TruthOrDare
import os

current_directory = os.getcwd()

token = TOD

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Load truth and dare questions from files
def load_questions(file_path):
    with open(file_path, "r") as file:
        questions = file.readlines()
    return questions

def write_questions(file_path, questions):
    with open(file_path, "w") as file:
        file.writelines(questions)

truth_file = current_directory + "\\truth_or_dare\\truth_file.txt"
dare_file = current_directory + "\\truth_or_dare\\dare_file.txt"

truth_questions = load_questions(truth_file)
dare_questions = load_questions(dare_file)

# @tree.command(name="truth", description="gives you a random truth ☺️")
# async def clone_command(interation):
#     question = random.choice(truth_questions)
#     await interation.response.send_message(question)

# @tree.command(name="dare", description="gives you a random dare 😈")
# async def clone_command(interation):
#     dare = random.choice(dare_questions)
#     await interation.response.send_message(dare)

@tree.command(name="addtruth", description="add a truth to the file")
async def add_truth_command(interaction, *, truth: str):
    truth_questions.append(truth + "\n")
    write_questions(truth_file, truth_questions)
    await interaction.response.send_message(f"Added truth: {truth}")

@tree.command(name="adddare", description="add a dare to the file")
async def add_dare_command(interaction, *, dare: str):
    dare_questions.append(dare + "\n")
    write_questions(dare_file, dare_questions)
    await interaction.response.send_message(f"Added dare: {dare}")

@tree.command(name="dare", description="gives you a random dare 😈")
async def dare_from_console_command(interaction):
    # only send to console if person using the command is the id 693128994488320001
    if interaction.user.id == 693128994488320001 or interaction.user.id == 851777628352282634:
        await interaction.response.send_message("thinking of new dare...", ephemeral=True)
        dare = input("Enter a dare: ")
        if dare == "!":
            dare = random.choice(dare_questions)
        await interaction.followup.send(dare)
    else:
        dare = random.choice(dare_questions)
        await interaction.response.send_message(dare)

@tree.command(name="truth", description="gives you a random truth ☺️")
async def truth_from_console_command(interaction):
    # only send to console if person using the command is the id 693128994488320001
    if interaction.user.id == 693128994488320001 or interaction.user.id == 851777628352282634:
        await interaction.response.send_message("thinking of new truth...", ephemeral=True)
        truth = input("Enter a truth: ")
        if truth == "!":
            truth = random.choice(truth_questions)
        await interaction.followup.send(truth)
    else:
        truth = random.choice(truth_questions)
        await interaction.response.send_message(truth)

@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/dares or /truths"))

client.run(TOD)