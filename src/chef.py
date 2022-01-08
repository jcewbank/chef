# Python 2.x warn
import sys
if sys.version_info < (3,0):
    print("This module requires python 3.x. Exiting.")
    exit()

from pathlib import Path
import argparse
import server
import credentials

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