import discord
from discord.ext import commands
import ctx
import re
import time
from time import sleep
import asyncio
from dis_token import *

token = Enigma

PREFIX = "$"
bot = commands.Bot(command_prefix=PREFIX, description="Hi")

class colors:
    default = 0
    teal = 0x1abc9c
    dark_teal = 0x11806a
    green = 0x2ecc71
    dark_green = 0x1f8b4c
    blue = 0x3498db
    dark_blue = 0x206694
    purple = 0x9b59b6
    dark_purple = 0x71368a
    magenta = 0xe91e63
    dark_magenta = 0xad1457
    gold = 0xf1c40f
    dark_gold = 0xc27c0e
    orange = 0xe67e22
    dark_orange = 0xa84300
    red = 0xe74c3c
    dark_red = 0x992d22
    lighter_grey = 0x95a5a6
    dark_grey = 0x607d8b
    light_grey = 0x979c9f
    darker_grey = 0x546e7a
    blurple = 0x7289da
    greyple = 0x99aab5

@bot.event
async def on_ready():
    print('Logged on as', bot.user)
    channel = bot.get_channel(717005397655027805)
    #await channel.send("I am now online")
    activity = discord.Game(name="le!help", type=3)
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.command()
async def test(message):
    color = colors.blue
    embedVar = discord.Embed(
       title="Law enforcement Help", description="law enforcement bot was created by killer ninjas and klleoo as a project to incorporate a court like system to discord.", color=color)
    embedVar.add_field(name="Common Commands", value="le!help, le!color, /court @user {original punishment assesment in seconds}", inline=False)
    embedVar.add_field(name="How to add the bot to your server", value="To add the bot to your server click [here](https://discord.com/api/oauth2/authorize?client_id=837206682596933633&permissions=2416208976&scope=bot)", inline=False)
    await message.channel.send(embed=embedVar)

@commands.has_role("Server Developer")
@bot.command()
async def court(ctx, user_mentioned: discord.Member, time: int):
    user_id = ctx.message.mentions[0].id
    user = ctx.message.mentions[0]
    role = discord.utils.get(ctx.message.guild.roles, name="Jail")
    await user_mentioned.add_roles(role)
    await ctx.send(
        f"sending <@{user_id}> to court!"
    )
    await asyncio.sleep(time)
    await user_mentioned.remove_roles(role)

bot.run(token)