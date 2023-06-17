import discord
from discord import app_commands
from dis_token import *

token = Enigma

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

MORSE_CODE_DICT = {'A': '.-', 'B': '-...',
                   'C': '-.-.', 'D': '-..', 'E': '.',
                   'F': '..-.', 'G': '--.', 'H': '....',
                   'I': '..', 'J': '.---', 'K': '-.-',
                   'L': '.-..', 'M': '--', 'N': '-.',
                   'O': '---', 'P': '.--.', 'Q': '--.-',
                   'R': '.-.', 'S': '...', 'T': '-',
                   'U': '..-', 'V': '...-', 'W': '.--',
                   'X': '-..-', 'Y': '-.--', 'Z': '--..',
                   '1': '.----', '2': '..---', '3': '...--',
                   '4': '....-', '5': '.....', '6': '-....',
                   '7': '--...', '8': '---..', '9': '----.',
                   '0': '-----', ', ': '--..--', '.': '.-.-.-',
                   '?': '..--..', '/': '-..-.', '-': '-....-',
                   '(': '-.--.', ')': '-.--.-'}


def encrypt(message):
    cipher = ''
    for letter in message:
        if letter != ' ':
            cipher += MORSE_CODE_DICT[letter] + ' '
        else:
            cipher += ' '

    return cipher


def decrypt(message):
    message += ' '

    decipher = ''
    citext = ''
    for letter in message:
        if letter != ' ':
            i = 0
            citext += letter
        else:
            i += 1
            if i == 2:
                decipher += ' '
            else:
                decipher += list(MORSE_CODE_DICT.keys())[list(MORSE_CODE_DICT.values()).index(citext)]
                citext = ''

    return decipher


@tree.command(name="encrypt", description="Encrypts a message into Morse code")
async def encrypt_command(interaction, message: str):
    result = encrypt(message.upper())
    await interaction.response.send_message(result, ephemeral=False)


@tree.command(name="decrypt", description="Decrypts a Morse code message")
async def decrypt_command(interaction, message: str):
    result = decrypt(message)
    await interaction.response.send_message(result, ephemeral=True)


@tree.command(name="help", description="Displays the help message")
async def help_command(interaction):
    color = discord.Color.green()
    embed = discord.Embed(title="Morse Code Bot Help", color=color)

    encrypt_command_help = "Encrypt a message into Morse code.\n" \
                           "**Usage:** /encrypt <message>\n" \
                           "**Example:** /encrypt Hello"

    decrypt_command_help = "Decrypt a Morse code message.\n" \
                           "**Usage:** /decrypt <message>\n" \
                           "**Example:** /decrypt .... . .-.. .-.. ---"

    embed.add_field(name="Encrypt Command", value=encrypt_command_help, inline=False)
    embed.add_field(name="Decrypt Command", value=decrypt_command_help, inline=False)

    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    await tree.sync()
    print("Ready!")
    await client.change_presence(activity=discord.Game(name="/help"))

client.run(token)