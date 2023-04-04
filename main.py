import disnake
from disnake.ext import commands
from yt_dlp import YoutubeDL
import config

bot = commands.Bot(command_prefix = '!', intents = disnake.Intents.all())

@bot.event
async def on_ready():
    print("Hello world!")

@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        await message.reply("sam takoi")

bot.run(config.token)