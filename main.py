import disnake
from disnake.ext import commands
from yt_dlp import YoutubeDL

import config

bot = commands.Bot(command_prefix = '!', intents = disnake.Intents.all())
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': "True", 'simulate': 'True', 'key': 'FFmpegExtractAudio'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

vcs = {}

@bot.event
async def on_ready():
    print("Hello world!")

@bot.command()
async def play(ctx, url: str):
    print(url)
    try:
        vc = await ctx.author.voice.channel.connect()
        vcs[vc.guild.id] = vc
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            info = ytdl.extract_info(url, download=False)
        link = info.get("url", None)
        title = info['title']

        vcs[ctx.guild.id].play(disnake.FFmpegPCMAudio(
            source=link, **FFMPEG_OPTIONS))

    except:
        await ctx.send("подключись к каналу, баран")

bot.run(config.token)