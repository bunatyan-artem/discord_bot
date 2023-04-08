import disnake
import asyncio
from disnake.ext import commands
from yt_dlp import YoutubeDL

import config

bot = commands.Bot(command_prefix = '!!', intents = disnake.Intents.all())
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': False, 'simulate': True, 'key': 'FFmpegExtractAudio',
                'forceduration': True, 'quiet': True, 'no_warnings': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

vcs = {}
queue_list = {}
repeat_flag = {}
pause_flag = {}

@bot.event
async def on_ready():
    print("bot is on")

@bot.command()
async def play(ctx, url: str):
    """order a song (use URL from YT or just type the song's name)"""
    vc = ctx.guild.voice_client
    try:
        if not vc:
            vc = await ctx.author.voice.channel.connect()
            queue_list[ctx.guild.id] = []
            repeat_flag[ctx.guild.id] = False
            pause_flag[ctx.guild.id] = False
            song = 0
        vcs[vc.guild.id] = vc
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if 'https://' in url:
                info = ytdl.extract_info(url, download = False)
            else:
                info = ytdl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
        queue_list[ctx.guild.id].append(info)
        if not vc.is_playing():
            while True:
                if len(queue_list[ctx.guild.id]) == 0:
                    await vcs[ctx.guild.id].disconnect()
                    break
                link = queue_list[ctx.guild.id][song].get("url", None)
                if repeat_flag:
                    song += 1
                    if song == len(queue_list[ctx.guild.id]):
                        song = 0
                vcs[ctx.guild.id].play(disnake.FFmpegPCMAudio(source = link, **FFMPEG_OPTIONS))
                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(2)
                if len(queue_list[ctx.guild.id]) > 0 and not repeat_flag[ctx.guild.id]:
                    queue_list[ctx.guild.id].pop(0)
                elif not repeat_flag[ctx.guild.id] or not vc.is_connected():
                    break

    except:
        await ctx.send("ошибка (play)")

@bot.command()
async def pause(ctx):
    """pause/resume playback"""
    try:
        if pause_flag[ctx.guild.id]:
            pause_flag[ctx.guild.id] = False
            vcs[ctx.guild.id].resume()
        else:
            pause_flag[ctx.guild.id] = True
            vcs[ctx.guild.id].pause()
    except:
        await ctx.send("ошибка")

@bot.command()
async def skip(ctx):
    """skip current track"""
    try:
        vcs[ctx.guild.id].stop()
    except:
        await ctx.send("ошибка")

@bot.command()
async def wrong(ctx):
    """remove last added track"""
    try:
        queue_list[ctx.guild.id].pop()
    except:
        await ctx.send("ошибка")

@bot.command()
async def stop(ctx):
    """stop playback"""
    try:
        vcs[ctx.guild.id].stop()
        await vcs[ctx.guild.id].disconnect()
    except:
        await ctx.send("ошибка")

@bot.command()
async def repeat(ctx):
    """toogle repeat mode for current track"""
    try:
        if repeat_flag[ctx.guild.id]:
            repeat_flag[ctx.guild.id] = False
        else:
            repeat_flag[ctx.guild.id] = True
    except:
        await ctx.send("ошибка")

@bot.command()
async def queue(ctx):
    """print current queue"""
    try:
        queue_text = "Queue:\n"
        for i in range(len(queue_list[ctx.guild.id])):
            queue_text += f"{i + 1}) {queue_list[ctx.guild.id][i]['title']}\n"
        await ctx.send(queue_text)
    except:
        await ctx.send("ошибка")

bot.run(config.token)