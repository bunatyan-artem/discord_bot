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

@bot.event
async def on_ready():
    print("bot is on")

@bot.command()
async def play(ctx, request: str):
    """order a song (use URL from YT or just type the song's name)"""
    vc = ctx.guild.voice_client
    try:
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if 'https://' in request:
                info = ytdl.extract_info(request, download = False)
            else:
                try:
                    info = ytdl.extract_info(f"ytsearch:{request}", download=False)['entries'][0]
                    await ctx.send(f"{info['webpage_url']}\n{info['duration_string']}")
                except:
                    await ctx.send(f'не могу найти в ютубе "{request}"')
                    return
        if not vc:
            vc = await ctx.author.voice.channel.connect()
            queue_list[ctx.guild.id] = []
            repeat_flag[ctx.guild.id] = False
            song = 0
        vcs[vc.guild.id] = vc
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
        if vcs[ctx.guild.id].is_paused():
            vcs[ctx.guild.id].resume()
        else:
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
    """toogle repeat mode for current queue"""
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