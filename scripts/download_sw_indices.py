import wget
import os
from pathlib import Path

def main():

    home = str(Path.home())
    download_dir=f'{home}/data/raw/indices'
    downloaded_files = download_all_indices(download_dir)
    print(f"downloaded files: {downloaded_files}")

def download_all_indices(download_dir: str):

    url1 = 'https://sol.spacenvironment.net/JB2008/indices/SOLFSMY.TXT'
    url2 = 'https://sol.spacenvironment.net/JB2008/indices/DTCFILE.TXT'
    url3 = 'https://www.celestrak.com/SpaceData/SW-All.csv'

    downloaded_files = []

    for url in [url1,url2,url3]:
        print(f"downloading {url}")
        outdir = wget.download(url,download_dir)
        print(f'downloaded at {outdir}')
        downloaded_files.append(outdir)
    
    return downloaded_files
    
if __name__ == "__main__":
    main()
