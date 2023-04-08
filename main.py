import disnake
import asyncio
from disnake.ext import commands
from yt_dlp import YoutubeDL

import config

bot = commands.Bot(command_prefix = '!', intents = disnake.Intents.all())
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': "True", 'simulate': 'True', 'key': 'FFmpegExtractAudio'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

vcs = {}
queue = {}

@bot.event
async def on_ready():
    print("bot is on")

@bot.command()
async def play(ctx, url: str):
    vc = ctx.guild.voice_client
    try:
        if not vc:
            vc = await ctx.author.voice.channel.connect()
        vcs[vc.guild.id] = vc
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            info = ytdl.extract_info(url, download = False)
        if ctx.guild.id not in queue:
            queue[ctx.guild.id] = []
        queue[ctx.guild.id].append(info)
        if not vc.is_playing():
            while True:
                if len(queue[ctx.guild.id]) == 0:
                    await vcs[ctx.guild.id].disconnect()
                    break
                link = queue[ctx.guild.id][0].get("url", None)
                vcs[ctx.guild.id].play(disnake.FFmpegPCMAudio(source = link, **FFMPEG_OPTIONS))
                while vc.is_playing():
                    await asyncio.sleep(1)
                if len(queue[ctx.guild.id]) > 0:
                    queue[ctx.guild.id].pop(0)
                else:
                    break

    except:
        await ctx.send("ошибка")

bot.run(config.token)