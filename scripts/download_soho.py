import subprocess
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

output_dir = "/home/ga00693/2024-HL-Thermo-CL/data/soho_data_raw"
base_url = "https://lasp.colorado.edu/eve/data_access/eve_data/lasp_soho_sem_data/long/15_sec_avg/"

years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 
        2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

def download_year_data(year):
    directory = f"{output_dir}/{year}"
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
        f"{base_url}{year}/",
    ]

    subprocess.run(wget_command, cwd=directory)
    return year

# let's parallelize the download to save time
with ThreadPoolExecutor() as executor:  # in case needed, use the max_workers argument to limit the number of workers
    futures = [executor.submit(download_year_data, year) for year in years]
    for future in as_completed(futures):
        year = future.result()
        print(f"Completed download for year: {year}")
