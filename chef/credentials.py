import json

# TODO This should handle guilds but I can't be bothered atm

class Credentials:
    _token = ""
    users = {}
    channels = {}
    
    def __init__(self, fpath):
        # Open and parse the JSON credentials file
        with open(fpath, 'r') as json_file:
            data = json.load(json_file)
            self._token = data["token"]
            if "users" in data:
                self.users = data["users"]
            if "channels" in data:
                self.channels = data["channels"]
                
    def getToken(self):
        return self._token