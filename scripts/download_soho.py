import subprocess
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import datetime


date = "2022-01-01"
a_date = datetime.datetime.strptime(date, "%Y-%m-%d")

class SohoDownloader:
    def __init__(self, output_dir: str):
        self.base_url = "https://lasp.colorado.edu/eve/data_access/eve_data/lasp_soho_sem_data/long/15_sec_avg/"
        self.output_dir = output_dir

    def download_one_year_data(self, year: int):

        directory = f"{self.output_dir}/{year}"
        os.makedirs(directory, exist_ok=True)
        wget_command = [
            "wget",
            "-r",
            "-np",
            "-nH",
            "--cut-dirs=7",
            "-A",
            "*.00",
            "--reject",
            "index.html*",
            "--tries=5",  # Retry up to 5 times
            "--waitretry=2",  # Wait 2 seconds between retries
            f"{self.base_url}{year}/",
        ]

        subprocess.run(wget_command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return year

    def download_data_parallel(self, years: list[int]):
        # let's parallelize the download to save time
        with ThreadPoolExecutor() as executor:  # in case needed, use the max_workers argument to limit the number of workers
            futures = [executor.submit(self.download_one_year_data, year) for year in years]
            for future in as_completed(futures):
                year = future.result()
                print(f"Completed download for year: {year}")

def get_all_years() -> list[int]:
    """
    Get all years from 2000 until the present. 
    """
    START_YEAR = 2000
    now = datetime.datetime.now()
    this_year = now.year
    all_years = list(range(START_YEAR, this_year+1))
    return all_years

def main():

    output_dir = "/shared/raw/soho"
    base_url = "https://lasp.colorado.edu/eve/data_access/eve_data/lasp_soho_sem_data/long/15_sec_avg/"


    years = get_all_years()


    downloader = SohoDownloader(output_dir, base_url)
    downloader.download_data_parallel(years)



if __name__ == "__main__":
    main()
