import os
import requests
from datetime import datetime
from pathlib import Path
import wget


def download_file(url: str, output_path: str) -> str:
    """Download a file from URL to output_path using requests."""
    print(f"Downloading from {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error for bad status codes

    # Write the file in chunks
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f'Downloaded to {output_path}')
    return output_path


def main():

    output_dir = '/shared/raw/goes'
    year = 2009

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    download_goes_one_year(year, output_dir)


def download_goes_one_year(year, output_dir):
    download_finished_missions(year, output_dir)
    download_active_missions(year, output_dir)


def download_active_missions(year: int, output_dir: str):
    g16_file = download_goes16(year, output_dir)
    g18_file = download_goes18(year, output_dir)
    

def download_finished_missions(year: int, output_dir: str):
    
    # These missions (14, 15 and 17) are now finished. 
    g14_file = download_goes14(year, output_dir=output_dir)
    g15_file = download_goes15(year, output_dir=output_dir)
    g18_file = download_goes17(year, output_dir=output_dir)


def download_goes14(year, output_dir):

    url1 = 'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/euvs/'

    y14 = [2009, 2010, 2012, 2015, 2016, 2017, 2018, 2019, 2020]

    # GOES 14 (not operational in 2024)
    if year in y14:
        download_dir = f'{output_dir}/goes14'
        os.makedirs(download_dir, exist_ok=True)
        dataurl = f"{url1}goes14/geuv-l2-avg1m/sci_geuv-l2-avg1m_g14_y{year}_v5-0-0.nc"
        output_file = f'{download_dir}/y{year}.nc'
        return download_file(dataurl, output_file)
    else: 
        return None

def download_goes15(year, output_dir):

    url1 = 'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/euvs/'
    y15 = list(range(2010,2020+1))

    #GOES 15 (not operational in 2024)
    if year in y15:
        download_dir = output_dir + '/goes15'
        os.makedirs(download_dir, exist_ok=True)
        dataurl = f'{url1}goes15/geuv-l2-avg1m/sci_geuv-l2-avg1m_g15_y{year}_v5-0-0.nc'
        output_file = f'{download_dir}/y{year}.nc'
        return download_file(dataurl, output_file)
    else:
        return None

def download_goes16(year, output_dir):

    this_year = datetime.now().year
    y16 = list(range(2017,this_year+1))
    url2 = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'
    version = "v1-0-6"

    # GOES 16 (operational in 2024)
    if year in y16:
        download_dir = output_dir + '/goes16'
        os.makedirs(download_dir, exist_ok=True)
        dataurl = f"{url2}goes16/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g16_y{year}_{version}.nc"
        output_file = f'{download_dir}/y{year}.nc'
        return download_file(dataurl, output_file)
    else:
        return None


def download_goes17(year, output_dir):
    url2 = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'

    #GOES 17 (not operational in 2024)
    y17 = list(range(2018,2023+1))
    if year in y17:
        download_dir = output_dir + '/goes17'
        os.makedirs(download_dir, exist_ok=True)
        dataurl = f'{url2}goes17/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g17_y{year}_v1-0-4.nc'
        output_file = f'{download_dir}/y{year}.nc'
        return download_file(dataurl, output_file)
    else:
        return None



def download_goes18(year, output_dir):
    url2 = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'
    this_year = datetime.now().year
    y18 = list(range(2022,this_year+1))
    version = "v1-0-6"

    #GOES 18 (operational in 2024)
    if year in y18:
        download_dir = output_dir + '/goes18'
        os.makedirs(download_dir, exist_ok=True)
        dataurl = f'{url2}goes18/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g18_y{year}_{version}.nc'
        output_file = f'{download_dir}/y{year}.nc'
        return download_file(dataurl, output_file)

    else:
        return None

if __name__ == "__main__":
    main()
