from pathlib import Path
import os
import webutils
import shutil
import json
import difflib

###
# Emojis are generally stored in (emoji:filename) and (emoji:url) pairs
###

class EmojiCache:
    _emoji_pngs = []
    _init = False
    _fresh = False
    _guilds = None
    
    # JSON Constants
    _EMOJIFILES = 'emoji_files'
    _EMOJIURLS = 'emoji_urls'
    _GUILDNAME = 'guild_name'
    _GUILDID = 'guild_id'
    
    # Cache layout:
    # { 
    #   <guild_id> : 
    #   { 
    #       name : <guild_name>,
    #       id : <guild_id>, 
    #       emojis : 
    #           [(<emoji_name> : <emoji_filename>), ...] } 
    # }
    _cache = {}
    
    def __init__(self):
        # Try reading in persistent registries
        customPath = Path('emojis/custom/')
        if not customPath.exists():
            os.makedirs(customPath)
        subDirs = next(os.walk(customPath))[1]
        for sd in subDirs:
            # Check for an emojis.json file in each subdir
            self._refreshGuildReg(customPath / sd)
    
    # Update the emoji registry
    # We always start over from scratch
    def _writeGuildReg(self, guild, path, files, urls):
        data = {}
        data[self._GUILDNAME] = guild.name
        data[self._GUILDID] = guild.id
        data[self._EMOJIFILES] = {}
        data[self._EMOJIURLS] = {}
        for i in zip(files, urls):
            data[self._EMOJIFILES][i[0][0]] = i[0][1]   # {'troll':'troll.jpg'}
            data[self._EMOJIURLS][i[0][0]] = i[1]       # {'troll':'https://cdn.discordapp.com//emojis/720440736251641957.png'}
        # serialize
        outFile = Path(path) / 'emojis.json'
        with open(outFile, 'w') as json_file:
            json.dump(data, json_file)
            
    def _writeGuildCache(self, guild, files, urls):
        data = {}
        data[self._GUILDNAME] = guild.name
        data[self._GUILDID] = guild.id
        data[self._EMOJIFILES] = {}
        data[self._EMOJIURLS] = {}
        for i in zip(files, urls):
            data[self._EMOJIFILES][i[0][0]] = i[0][1]
            data[self._EMOJIURLS][i[0][0]] = i[1]
        # cache
        self._cache[str(guild.id)] = data
            
    def _refreshGuildReg(self, guildFolder):
        entries = []
        sPath = guildFolder / "emojis.json"
        if sPath.exists():
            try:
                with open(sPath, 'r') as json_file:
                    data = json.load(json_file)
                    id = str(data[self._GUILDID])
                    name = data[self._GUILDNAME]
                    files = data[self._EMOJIFILES]
                    urls = data[self._EMOJIURLS]
                    self._cache[id] = {}
                    self._cache[id][self._GUILDID] = id
                    self._cache[id][self._GUILDNAME] = name
                    self._cache[id][self._EMOJIFILES] = files
                    self._cache[id][self._EMOJIURLS] = urls
            except BaseException as err:
                # Something is wrong with the JSON - delete it so next try refreshes
                print('EmojiCache exception. ' + f"Unexpected {err}, {type(err)}")
                shutil.rmtree(guildFolder)
        
    async def getFuzzyEmojiFilePath(self, guild, emoji_name):
        try:
            cached_guild = self._cache[str(guild.id)]
        except KeyError:
            # Try fetching the guild now
            (entries, _) = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        try:
            name = cached_guild[self._GUILDNAME]
            guildName = name.replace(' ', '_')
            entries = cached_guild[self._EMOJIFILES]
            eKeys = entries.keys()
            # difflib is overkill and doesn't match some normal substring use cases
            #eMatches = difflib.get_close_matches(emoji_name, eKeys)
            eMatches = [i for i in eKeys if emoji_name in i]
            if len(eMatches) > 0:
                return (Path(f'emojis/custom/{guildName}/'), eMatches)
        except KeyError:
            return None
        return (None, None)
        
    def getEmojiFilePath(self, guild, emoji_name):
        try:
            cached_guild = self._cache[str(guild.id)]
        except KeyError:
            # Try fetching the guild now
            entries, _ = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        try:
            name = cached_guild[self._GUILDNAME]
            guildName = name.replace(' ', '_')
            entries = cached_guild[self._EMOJIFILES]
            emojiPath = entries[emoji_name]
            filePath = Path(f'emojis/custom/{guildName}/{emojiPath}')
        except KeyError:
            return None
        return filePath
    
    def getEmojiList(self, guild):
        try:
            cached_guild = self._cache[str(guild.id)]
        except KeyError:
            # Try fetching the guild now
            entries, _ = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        l = []
        for key in cached_guild[self._EMOJIFILES].keys():
            l.append(key)
        l.sort()
        return l
    
    async def getEmojiURLs(self, guild, emoji_name):
        try:
            cached_guild = self._cache[str(guild.id)]
        except KeyError:
            # Try fetching the guild now
            (entries, _) = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        try:
            name = cached_guild[self._GUILDNAME]
            guildName = name.replace(' ', '_')
            entries = cached_guild[self._EMOJIURLS]
            eKeys = entries.keys()
            # difflib is overkill and doesn't match some normal substring use cases
            #eMatches = difflib.get_close_matches(emoji_name, eKeys)
            keyMatches = [i for i in eKeys if emoji_name in i]
            if len(keyMatches) > 0:
                urlMatches = [entries[i] for i in keyMatches]
                urlPairs = tuple(zip(keyMatches, urlMatches))
                return urlPairs
        except KeyError:
            return None
        return None
    
    # Takes a Discord guild object
    def fetchEmojis(self, guild):
        # sanitize the guild name
        guildName = guild.name.replace(' ', '_')
        emojiPath = Path('emojis')
        customPath = emojiPath / Path(f'custom/{guildName}')
        if not emojiPath.exists():
            os.mkdir(emojiPath)
        if not customPath.exists():
            os.mkdir(customPath)
        emojiFiles = []
        emojiURLs = []
        # Get all the custom emojis
        for e in guild.emojis:
            emojiURLs.append(webutils.unpackUrl(e.url))
            filename = f"{e.name}.png"
            emojiFiles.append((e.name, filename))
            webutils.download(e.url, customPath, filename)
        # Write the registry for this guild
        self._writeGuildReg(guild, customPath, emojiFiles, emojiURLs)
        self._writeGuildCache(guild, emojiFiles, emojiURLs)
        return (emojiFiles, emojiURLs)
            
    def clearEmojis(self, guild):
        self._cache.pop(str(guild.id), None)
        guildName = guild.name.replace(' ', '_')
        emojiPath = Path(f'emojis/custom/{guildName}')
        cnt = 0
        if emojiPath.exists():
            cnt = len([name for name in os.listdir(emojiPath) if os.path.isfile(os.path.join(emojiPath, name))])
            shutil.rmtree(emojiPath)
            return cnt
        else:
            print(f"path: {emojiPath.resolve()}")
            return 0