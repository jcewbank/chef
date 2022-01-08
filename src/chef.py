import argparse
import server
import credentials
from pathlib import Path

parser = argparse.ArgumentParser(description="Run the Chef bot")
parser.add_argument('--creds', help='credentials JSON file', type=str, nargs='?', default="cred.json")

args = parser.parse_args()

fpath = Path(args.creds)
if fpath.exists():
    creds = credentials.Credentials(fpath)
    server.run(creds)