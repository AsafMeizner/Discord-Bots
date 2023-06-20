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
async def encrypt_command(interation, seed: str, message: str):
    encrypted_message = encrypt(message, seed)
    for i in range(0, 6):
        encrypted_message = encrypt(encrypted_message, seed)

    await interation.response.send_message("Message sent!", ephemeral=True)

    # Create a webhook using the command invoker as the cloned user
    webhook = await interation.channel.create_webhook(name=interation.user.display_name)

    # Send the encrypted message as the cloned user
    await webhook.send(content=":lock: " + encrypted_message, username=interation.user.display_name, avatar_url=interation.user.avatar.url)
    # await webhook.send(content=encrypted_message, username="hi")

    await webhook.delete()

@tree.command(name="who-am-i", description="types the name of the user who typed the command") 
async def who_am_i_command(ctx):
    await ctx.send(ctx.author.display_name)



@tree.command(name="decrypt", description="Decrypts a message with a seed")
async def decrypt_command(interaction, seed: str, message: str):    
    decrypted_message = decrypt(message, seed)
    for i in range(0, 6):
        decrypted_message = decrypt(decrypted_message, seed)

    # Reply with the decrypted message
    await interaction.response.send_message(":unlock: " + decrypted_message, ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/help"))

client.run(token)