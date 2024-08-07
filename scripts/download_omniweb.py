import os
import subprocess
from datetime import datetime

# Define the initial start date and the end date
years=range(2000,2025)
year_end=2024
start_date = datetime.strptime("20000101", "%Y%m%d")
end_date = datetime.strptime("20240531", "%Y%m%d")

base_url = "https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi"
fixed_params = "activity=retrieve&res=min&spacecraft=omni_min&vars=11&vars=12&vars=13&vars=14&vars=15&vars=16&vars=17&vars=18&vars=19&vars=20&vars=21&vars=22&vars=23&vars=24&vars=25&vars=26&vars=27&vars=28&vars=29&vars=30&vars=31&vars=32&vars=33&vars=34&vars=35&vars=36&vars=37&vars=38&vars=39&vars=40&vars=41&vars=42&scale=Linear&ymin=&ymax=&view=0&charsize=&xstyle=0&ystyle=0&symbol=0&symsize=&linestyle=solid&table=0&imagex=640&imagey=480&color=&back="
omiweb_data_dir='../data/omniweb_data_raw'
os.makedirs(omiweb_data_dir, exist_ok=True)  # Ensure local directory exists

# Loop over each year and generate the command
for year in years:
    if year==2024:    
        start_date = str(year)+"0101"
        end_date = str(year)+"0531"
    else:
        start_date = str(year)+"0101"
        end_date = str(year)+"1231"
    
    
    # Generate the wget command
    output_file = os.path.join(omiweb_data_dir,f"data_{start_date}_{end_date}.txt")
    print('check if already exists')
    if os.path.exists(output_file)==False:
        wget_command = f"sudo wget --post-data \"{fixed_params}&start_date={start_date}&end_date={end_date}\" {base_url} -O {output_file}"
    
        # Execute the wget command
        print(f"Running command: {wget_command}")
        subprocess.run(wget_command, shell=True)
    else:
        print('file already exists, moving to the next one')
        