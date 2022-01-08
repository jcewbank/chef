from pathlib import Path
import os
import webutils
import shutil
import json

###
# Emojis are generally stored in arrays of tuple pairs (entries) where each pair is
# (emoji name, filename)
###

class EmojiCache:
    _emoji_pngs = []
    _init = False
    _fresh = False
    _guilds = None
    
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
            os.mkdir(customPath)
        subDirs = next(os.walk(customPath))[1]
        for sd in subDirs:
            # Check for an emojis.json file in each subdir
            self._refreshGuildReg(customPath / sd)
    
    # Update the emoji registry
    # We always start over from scratch
    def _writeGuildReg(self, guild, path, entries):
        data = {}
        data["guild_name"] = guild.name
        data["guild_id"] = guild.id
        data["emojis"] = {}
        for e in entries:
            data["emojis"][e[0]] = e[1]
        # serialize
        outFile = Path(path) / 'emojis.json'
        with open(outFile, 'w') as json_file:
            json.dump(data, json_file)
            
    def _writeGuildCache(self, guild, entries):
        data = {}
        data["guild_name"] = guild.name
        data["guild_id"] = guild.id
        data["emojis"] = {}
        for e in entries:
            data["emojis"][e[0]] = e[1]
        # cache
        self._cache[str(guild.id)] = data
            
    def _refreshGuildReg(self, guildFolder):
        entries = []
        sPath = guildFolder / "emojis.json"
        if sPath.exists():
            try:
                with open(sPath, 'r') as json_file:
                    data = json.load(json_file)
                    id = str(data["guild_id"])
                    name = data["guild_name"]
                    entries = data["emojis"]
                    self._cache[id] = {}
                    self._cache[id]["guild_id"] = id
                    self._cache[id]["guild_name"] = name
                    self._cache[id]['emojis'] = entries
            except KeyError:
                # Something is wrong with the JSON - delete it so next try refreshes
                shutil.rmtree(guildFolder)
        
    def getEmojiFilePath(self, guild, emoji_name):
        try:
            cached_guild = self._cache[str(guild.id)]
        except KeyError:
            # Try fetching the guild now
            entries = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        try:
            name = cached_guild["guild_name"]
            guildName = name.replace(' ', '_')
            entries = cached_guild["emojis"]
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
            entries = self.fetchEmojis(guild)
            if len(entries) == 0:
                return None
            cached_guild = self._cache[str(guild.id)]
        l = []
        for key in cached_guild["emojis"].keys():
            l.append(key)
        l.sort()
        return l

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
        got = []
        # Get all the custom emojis
        for e in guild.emojis:
            filename = f"{e.name}.png"
            got.append((e.name, filename))
            webutils.download(e.url, customPath, filename)
        # Write the registry for this guild
        self._writeGuildReg(guild, customPath, got)
        self._writeGuildCache(guild, got)
        return got
            
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