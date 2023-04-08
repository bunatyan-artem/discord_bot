import disnake
import asyncio
from disnake.ext import commands
from yt_dlp import YoutubeDL

import config

bot = commands.Bot(command_prefix = '!!', intents = disnake.Intents.all())
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': "True", 'simulate': 'True', 'key': 'FFmpegExtractAudio'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

vcs = {}
queue = {}
repeat_flag = {}

@bot.event
async def on_ready():
    print("bot is on")

@bot.command()
async def play(ctx, url: str):
    vc = ctx.guild.voice_client
    try:
        if not vc:
            vc = await ctx.author.voice.channel.connect()
            queue[ctx.guild.id] = []
            repeat_flag[ctx.guild.id] = False
            song = 0
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
                link = queue[ctx.guild.id][song].get("url", None)
                if repeat_flag:
                    song += 1
                    if song == len(queue[ctx.guild.id]):
                        song = 0
                vcs[ctx.guild.id].play(disnake.FFmpegPCMAudio(source = link, **FFMPEG_OPTIONS))
                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(1)
                if len(queue[ctx.guild.id]) > 0 and not repeat_flag[ctx.guild.id]:
                    queue[ctx.guild.id].pop(0)
                elif not repeat_flag[ctx.guild.id] or not vc.is_connected():
                    break

    except:
        await ctx.send("ошибка (play)")

@bot.command()
async def pause(ctx):
    try:
        vcs[ctx.guild.id].pause()
    except:
        await ctx.send("ошибка")

@bot.command()
async def stop(ctx):
    try:
        vcs[ctx.guild.id].stop()
        await vcs[ctx.guild.id].disconnect()
    except:
        await ctx.send("ошибка")

@bot.command()
async def resume(ctx):
    try:
        vcs[ctx.guild.id].resume()
    except:
        await ctx.send("ошибка")

@bot.command()
async def repeat(ctx):
    if repeat_flag[ctx.guild.id]:
        repeat_flag[ctx.guild.id] = False
    else:
        repeat_flag[ctx.guild.id] = True

bot.run(config.token)