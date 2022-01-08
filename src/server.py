import os
import discord
import strings
import random
from pathlib import Path
import webutils
import emojicache as ec
import textwrap
import time
import re

from discord.errors import HTTPException

client = discord.Client()

_guilds = []
_emojiCache = None
_creds = None

#_banned_words = ["howdy","howdily","huu"]

# Flags
alan_go_to_bed = 0
last_daily = 0

# RE
reg_hi = r'[Hh][IiUu]+\b'
regc_hi = re.compile(reg_hi)

def get_emoji(name, emojis):
    try:
        emoji = next(filter(lambda x: x.name==name, emojis))
        return emoji
    except BaseException as err:
        return name
    
async def handle_infractions(message):
    global _creds
    if str(message.channel.id) != _creds.channels.get("channel_hi"):
        found = False
        c = message.content.lower()
        if regc_hi.match(message.content) is not None:
            await message.add_reaction(get_emoji("squirrel", message.guild.emojis))
            return
            
async def handle_emoji(message):
    global _emojiCache
    try:
        #if message.content.startswith('!eval '):
        #    s = message.content[6:]
        #    print('Doing eval "' + s + '"')
        #    out = str(eval(s))
        #    if out != '':
        #        await message.channel.send(out)
        #    else:
        #        await message.channel.send('done')
        if message.content.startswith('!writeReg'):
            got = []
            guildName = message.guild.name.replace(' ', '_')
            for e in message.guild.emojis:
                filename = f"{e.name}.png"
                got.append((e.name, filename))
            _emojiCache.writeGuildReg(message.guild, f'emojis/custom/{guildName}', got)
        if message.content.startswith('!readReg'):
            got = _emojiCache.readGuildReg(message.guild)
            await message.channel.send(f'Emoji registry read complete\n{str(got)}')
        if message.content.startswith('!clearEmojis'):
            cnt = _emojiCache.clearEmojis(message.guild)
            await message.channel.send(f'Deleted {cnt} emojis')     
        if message.content.startswith('!fetchEmojis'):
            gotten = _emojiCache.fetchEmojis(message.guild)
            await message.channel.send(f'Got {len(gotten)} emojis')
        if message.content.startswith('!e '):
            emojiName = message.content.lower()[3:]
            # Try getting the file path from the cache
            emojiPath = _emojiCache.getEmojiFilePath(message.guild, emojiName)
            # Post the emoji to channel
            if emojiPath is None:
                await message.channel.send("can\'t find that emoji")
            else:
                await message.channel.send(file=discord.File(emojiPath))
        if message.content.lower() == ("!elist"):
            emojis = _emojiCache.getEmojiList(message.guild)
            # Format the output
            s = textwrap.fill(', '.join(emojis), 40)
            await message.channel.send(s)
            
    except BaseException as err:
        await message.channel.send('no. ' + f"Unexpected {err}, {type(err)}")

async def handle_alan(message, t):
    global alan_go_to_bed
    global _creds
    if str(message.author) == _creds.users.get("alan"):
        print('what to do about alan...')
        if alan_go_to_bed < 1 and t.tm_hour > 0 and t.tm.tm_hour < 3:
            print('before 3:00am -- light warning')
            alan_go_to_bed = 1
            message.channel.send('Alan go to bed.')
        elif alan_go_to_bed < 2 and t.tm_hour < 6:
            print('after 3:00am -- stern warning')
            alan_go_to_bed = 2
            message.channel.send('Alan it\'s past THREE AM. GO TO BED.')
        else:
            print('uh oh it\'s alan')
            alan_go_to_bed = 0
            message.channel.send('Alan thank you for sleeping.')

@client.event
async def on_ready():
    global _guilds
    global _emojiCache
    print('We have logged in as {0.user}'.format(client))
    async for g in client.fetch_guilds(limit=100):
        _guilds.append(g)
    print(str(_guilds))
    print('Connected to:')
    for g in _guilds:
        print('\t"' + str(g.name) + '" owned by "' + str(g.owner) + '"')
    _emojiCache = ec.EmojiCache()
    print(str(_emojiCache))
    
@client.event
async def on_message(message):
    global last_daily
    if message.author == client.user:
        return

    t = time.localtime()
    await handle_alan(message, t)
    
    await handle_infractions(message)
    
    if message.content.lower().startswith('hi') and len(message.content) > 3:
    #if len(message.content) > 3 and regc_hi.match(message.content) is not None:
        emoteName = message.content.lower()[3:]
        try:
            await message.add_reaction(get_emoji(emoteName, message.guild.emojis))
        except HTTPException as err:
            #await message.add_reaction("❌")
            pass
    elif message.content.lower().startswith('err'):
        await message.add_reaction("❌")
        
    if str(client.user.id) in message.content:
        if message.content.endswith('?'):
            idx = random.randrange(len(strings.responses))
            await message.channel.send(strings.responses[idx])
        
    await handle_emoji(message)

def run(creds):
    global _creds
    _creds = creds
    client.run(_creds.getToken())
