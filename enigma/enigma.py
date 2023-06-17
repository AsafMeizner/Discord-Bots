import discord
from discord import app_commands
import random
from dis_token import *

token = Enigma

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SEED_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
SEED_LENGTH = 16


def generate_character_map(seed):
    random.seed(seed)
    character_map = list(SEED_ALPHABET)
    random.shuffle(character_map)
    return character_map


def encrypt(message, seed):
    character_map = generate_character_map(seed)
    encrypted_message = ""

    for char in message:
        if char in SEED_ALPHABET:
            index = SEED_ALPHABET.index(char)
            encrypted_message += character_map[index]
        else:
            encrypted_message += char

    return encrypted_message


def decrypt(message, seed):
    character_map = generate_character_map(seed)
    decrypted_message = ""

    for char in message:
        if char in SEED_ALPHABET:
            index = character_map.index(char)
            decrypted_message += SEED_ALPHABET[index]
        else:
            decrypted_message += char

    return decrypted_message


@tree.command(name="encrypt", description="Encrypts a message with a seed")
async def encrypt_command(interaction, seed: str, message: str):
    result = encrypt(message, seed)
    await interaction.response.send_message(result, ephemeral=False)


@tree.command(name="decrypt", description="Decrypts a message with a seed")
async def decrypt_command(interaction, seed: str, message: str):
    result = decrypt(message, seed)
    await interaction.response.send_message(result, ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/help"))

client.run(token)
