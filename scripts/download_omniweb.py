import os
import subprocess
from datetime import datetime, timedelta
import calendar


def get_all_years() -> list[int]:
    """
    Get all years from 2000 until the present. 
    """
    now = datetime.now()
    this_year = now.year
    print(now, this_year)

    all_years = list(range(2000, this_year+1))
    print(all_years)
    return all_years

def get_last_day_of_previous_month():
    # Get the current date
    today = datetime.today()

    
    # First day of the current month
    first_day_current_month = today.replace(day=1)
    
    # Last day of the previous month is one day before the first day of the current month
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    
    return last_day_prev_month


def get_start_and_end_dates_per_month(year: int, month: int):
    """
    Get the start date and end date for a given month and year. 
    """

    start_date = f"{year}0101"

    # Get the last day of the month
    last_day_of_month = calendar.monthrange(year, month)[1]

    end_date = f"{year}{month:02}{last_day_of_month:02}"

    return start_date, end_date


def get_year_start_and_end_dates_single_year(year) -> tuple[str]:
    """
    Correct end date should be either 31st of December (if the year isn't this year), 
    or the last date of the previous month.
    
    Note that if today is the 1st of January this function should not be called.
    """

    start_date = str(year)+"0101"
    end_date = str(year)+"1231"

    if year == datetime.now().year:

        # yesterday as the lastdate -- doesn't work
        # today = datetime.today()
        # yesterday = today - timedelta(days=1)
        # end_date = yesterday.strftime("%Y%m%d")

        end_date = get_last_day_of_previous_month().strftime("%Y%m%d")

    # If it is January, we need to get the previous year. 
    if datetime.now().month == 1: 
        year =- 1


    return start_date, end_date, year

def download_omniweb_data_one_month(year:int, month:int, omiweb_data_dir: str): 
    """
    note year in YYYY format
    """
    start_date, end_date = get_start_and_end_dates_per_month(year, month)
    # Generate the wget command
    output_file_name = f"data_{year}_{month:02}.txt"
    output_file = os.path.join(omiweb_data_dir, output_file_name)
    return wget_omniweb_data(output_file, start_date, end_date)


def download_omniweb_data_one_year(year: int, omiweb_data_dir: str):
    """
    note year in YYYY format
    """
    start_date, end_date, year = get_year_start_and_end_dates_single_year(year)

    # Generate the wget command
    output_file_name = f"data_{year}.txt"
    output_file = os.path.join(omiweb_data_dir, output_file_name)
    return wget_omniweb_data(output_file, start_date, end_date)

def wget_omniweb_data(output_file, start_date, end_date):
    base_url = "https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi"
    fixed_params = "activity=retrieve&res=min&spacecraft=omni_min&vars=11&vars=12&vars=13&vars=14&vars=15&vars=16&vars=17&vars=18&vars=19&vars=20&vars=21&vars=22&vars=23&vars=24&vars=25&vars=26&vars=27&vars=28&vars=29&vars=30&vars=31&vars=32&vars=33&vars=34&vars=35&vars=36&vars=37&vars=38&vars=39&vars=40&vars=41&vars=42&scale=Linear&ymin=&ymax=&view=0&charsize=&xstyle=0&ystyle=0&symbol=0&symsize=&linestyle=solid&table=0&imagex=640&imagey=480&color=&back="

    
    file_already_exists = os.path.exists(output_file)
    if not file_already_exists:
        wget_command = f"wget --post-data \"{fixed_params}&start_date={start_date}&end_date={end_date}\" {base_url} -O {output_file}"
    
        # Execute the wget command
        print(f"Running command: {wget_command}")
        subprocess.run(wget_command, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return output_file
    else:
        print('file already exists, moving to the next one')
        return None

def download_omniweb_data(omiweb_data_dir):


    # All possible years of OMNIWEB data
    years = get_all_years()

    os.makedirs(omiweb_data_dir, exist_ok=True)  # Ensure local directory exists

    # Loop over each year and generate the command
    downloaded_files = []
    for year in years:
        output_file = download_omniweb_data_one_year(year=year, omiweb_data_dir=omiweb_data_dir)
        if output_file is not None:
            downloaded_files.append(output_file)
    return downloaded_files

def main():

    # 
    omiweb_data_dir='/shared/raw/omniweb'

    downloaded_files = download_omniweb_data(omiweb_data_dir=omiweb_data_dir)
    print(downloaded_files)


if __name__ == "__main__":
    main()
