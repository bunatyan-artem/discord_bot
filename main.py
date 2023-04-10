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

@bot.slash_command()
async def play(inter, request: str):
    """order a song (use URL from YT or just type the song's name)"""
    vc = inter.guild.voice_client
    try:
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if 'https://' in request:
                info = ytdl.extract_info(request, download = False)
                await inter.send(info['duration_string'])
            else:
                try:
                    info = ytdl.extract_info(f"ytsearch:{request}", download=False)['entries'][0]
                    await inter.send(f"{info['webpage_url']}\n{info['duration_string']}")
                except:
                    await inter.send(f'не могу найти в ютубе "{request}"')
                    return
        if not vc:
            vc = await inter.author.voice.channel.connect()
            queue_list[inter.guild.id] = []
            repeat_flag[inter.guild.id] = False
            song = 0
        vcs[vc.guild.id] = vc
        queue_list[inter.guild.id].append(info)
        if not vc.is_playing():
            while True:
                if len(queue_list[inter.guild.id]) == 0:
                    await vcs[inter.guild.id].disconnect()
                    break
                link = queue_list[inter.guild.id][song].get("url", None)
                if repeat_flag:
                    song += 1
                    if song == len(queue_list[inter.guild.id]):
                        song = 0
                vcs[inter.guild.id].play(disnake.FFmpegPCMAudio(source = link, **FFMPEG_OPTIONS))
                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(2)
                if len(queue_list[inter.guild.id]) > 0 and not repeat_flag[inter.guild.id]:
                    queue_list[inter.guild.id].pop(0)
                elif not repeat_flag[inter.guild.id] or not vc.is_connected():
                    break

    except:
        await inter.send("ошибка (play)")

@bot.slash_command()
async def pause(inter):
    """pause/resume playback"""
    try:
        if vcs[inter.guild.id].is_paused():
            vcs[inter.guild.id].resume()
            await inter.send("player resumed")
        else:
            vcs[inter.guild.id].pause()
            await inter.send("player paused")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def skip(inter):
    """skip current track"""
    try:
        vcs[inter.guild.id].stop()
        await inter.send("song skipped")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def wrong(inter):
    """remove last added track"""
    try:
        await inter.send(f"{queue_list[inter.guild.id][-1]['title']} was removed from queue")
        queue_list[inter.guild.id].pop()
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def stop(inter):
    """stop playback"""
    try:
        vcs[inter.guild.id].stop()
        await vcs[inter.guild.id].disconnect()
        await inter.send("player stopped")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def repeat(inter):
    """toggle repeat mode for current queue"""
    try:
        if repeat_flag[inter.guild.id]:
            repeat_flag[inter.guild.id] = False
        else:
            repeat_flag[inter.guild.id] = True
        await inter.send("Done")
        await asyncio.sleep(2)
        await inter.delete_original_response()
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def queue(inter):
    """print current queue"""
    try:
        queue_text = "Queue:\n"
        for i in range(len(queue_list[inter.guild.id])):
            queue_text += f"{i + 1}) {queue_list[inter.guild.id][i]['title']}\n"
        await inter.send(queue_text)
    except:
        await inter.send("ошибка")

bot.run(config.token)

@bot.command()
async def help(ctx):
    await ctx.send("There is no help..")