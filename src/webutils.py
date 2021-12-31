import requests
from pathlib import Path

def download(url, outDir, outName):
    p = Path(outDir)
    q = p / outName
    with open(q, 'wb') as outFile:
        content = requests.get(url, stream=True).content
        outFile.write(content)