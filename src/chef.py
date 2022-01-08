import argparse
import server
import credentials
from pathlib import Path

parser = argparse.ArgumentParser(description="Run the Chef bot")
parser.add_argument('--creds', \
    help='''Credentials for discord bot token, known users, and channels.
See credentials.json.example for an example.
(default: credentials.json)''', 
    type=str, nargs='?', default="credentials.json")

args = parser.parse_args()

fpath = Path(args.creds)
if fpath.exists():
    creds = credentials.Credentials(fpath)
    server.run(creds)