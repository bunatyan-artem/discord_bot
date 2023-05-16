import disnake
import openai
import asyncio
import sys
from disnake.ext import commands
from yt_dlp import YoutubeDL

import config

bot = commands.Bot(command_prefix = '!!', intents = disnake.Intents.all())
YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': False, 'simulate': True, 'key': 'FFmpegExtractAudio',
                'forceduration': True, 'quiet': True, 'no_warnings': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

openai.api_key = config.gpt_token

vcs = {}
queue_list = {}
repeat_flag = {}
gpt_chats = {}

@bot.event
async def on_ready():
    print("bot is on")

@bot.event
async def on_message(message):
    if message.guild or message.author.bot:
        return
    await gpt(message)

@bot.slash_command()
async def play(inter, request: str):
    """order a song (use URL from YT or just type the song's name)"""
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    vc = inter.guild.voice_client
    try:
        with YoutubeDL(YTDL_OPTIONS) as ytdl:
            if 'https://' in request:
                info = ytdl.extract_info(request, download = False)
                await inter.send(f"{request}\n{info['duration_string']}")
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
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
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
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    try:
        vcs[inter.guild.id].stop()
        await inter.send("song skipped")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def wrong(inter):
    """remove last added track"""
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    try:
        await inter.send(f"{queue_list[inter.guild.id][-1]['title']} was removed from queue")
        queue_list[inter.guild.id].pop()
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def stop(inter):
    """stop playback"""
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    try:
        vcs[inter.guild.id].stop()
        await vcs[inter.guild.id].disconnect()
        await inter.send("player stopped")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def repeat(inter):
    """toggle repeat mode for current queue"""
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    try:
        if repeat_flag[inter.guild.id]:
            repeat_flag[inter.guild.id] = False
            await inter.send("repeat mode off")
        else:
            repeat_flag[inter.guild.id] = True
            await inter.send("repeat mode on")
    except:
        await inter.send("ошибка")

@bot.slash_command()
async def queue(inter):
    """print current queue"""
    if not inter.guild:
        return await inter.send('В личных сообщениях я только gpt-бот')
    try:
        queue_text = "Queue:\n"
        for i in range(len(queue_list[inter.guild.id])):
            queue_text += f"{i + 1}) {queue_list[inter.guild.id][i]['title']}\n"
        await inter.send(queue_text)
    except:
        await inter.send("ошибка")

@bot.remove_command('help')
@bot.command()
async def help(ctx):
    await ctx.send("There is no help..")

@bot.slash_command()
async def off(inter, password : str):
    """don't use if you don't know"""
    if password == config.password:
        await inter.send("correct")
        sys.exit()
    else:
        await inter.send("wrong password")

@bot.slash_command()
async def gpt_clear(inter):
    """clear chat history with gpt-bot"""
    gpt_chats[inter.author.id] = []
    return await inter.send('Переписка стерта')

async def gpt(message):
    if message.author.id not in gpt_chats:
        gpt_chats[message.author.id] = []
    gpt_chat = gpt_chats[message.author.id]

    gpt_chat.append({'role': 'user', 'content': message.content})
    not_done = True
    while not_done:
        try:
            completion = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages = gpt_chat)
            not_done = False
        except:
            gpt_chat = gpt_chat[1:]

    chat_response = completion.choices[0].message.content
    gpt_chat.append({"role": "assistant", "content": chat_response})

    if chat_response.startswith('```'):
        chat_response = 'Code:\n' + chat_response
    messages = chat_response.split(sep = '```')

    for i in range(0, len(messages)):
        if i % 2 == 0:
            await reply(message, messages[i])
        else:
            first = messages[i].find('\n')
            lan = messages[i][:first]
            await reply(message, messages[i], is_code = True, lan = lan)

async def reply(message, text, is_code = False, lan = ''):
    if is_code and lan != '':
        text = text[len(lan):]

    while text != '':
        block = text[0:1980]
        if len(text) > 1980:
            last = block.rfind('\n')
            block = block[0:last]
        text = text.removeprefix(block)

        if is_code:
            block = f'```{lan}\n' + block + '\n```'
        await message.channel.send(block)

bot.run(config.token)