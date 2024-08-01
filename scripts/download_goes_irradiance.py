import os
import wget

output_dir = ''

if not os.path.isdir(output_dir+'goes'):
    os.mkdir(output_dir+'goes')

y14 = [2009, 2010, 2012, 2015, 2016, 2017, 2018, 2019, 2020]
y15 = list(range(2010,2020+1))
y16 = list(range(2017,2024+1))
y17 = list(range(2018,2023+1))
y18 = list(range(2022,2024+1))

url1 = 'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/euvs/'
url2 = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'

#GOES 14
for year in y14:
    dataurl = url1 + 'goes14' + '/geuv-l2-avg1m/sci_geuv-l2-avg1m_g14_y' + str(year) + '_v5-0-0.nc'
    download_dir = output_dir + 'goes/goes14_y' + str(year) + '.nc'
    wget_out_set = wget.download(dataurl,download_dir)
    print(f'downloaded at {wget_out_set}')

#GOES 15
for year in y15:
    dataurl = url1 + 'goes15' + '/geuv-l2-avg1m/sci_geuv-l2-avg1m_g15_y' + str(year) + '_v5-0-0.nc'
    download_dir = output_dir + 'goes/goes15_y' + str(year) + '.nc'
    wget_out_set = wget.download(dataurl,download_dir)
    print(f'downloaded at {wget_out_set}')

#GOES 16
for year in y16:
    dataurl = url2 + 'goes16' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g16_y' + str(year) + '_v1-0-4.nc'
    download_dir = output_dir + 'goes/goes16_y' + str(year) + '.nc'
    wget_out_set = wget.download(dataurl,download_dir)
    print(f'downloaded at {wget_out_set}')

#GOES 17
for year in y17:
    dataurl = url2 + 'goes17' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g17_y' + str(year) + '_v1-0-4.nc'
    download_dir = output_dir + 'goes/goes17_y' + str(year) + '.nc'
    wget_out_set = wget.download(dataurl,download_dir)
    print(f'downloaded at {wget_out_set}')

#GOES 18
for year in y18:
    dataurl = url2 + 'goes18' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g18_y' + str(year) + '_v1-0-4.nc'
    download_dir = output_dir + 'goes/goes18_y' + str(year) + '.nc'
    wget_out_set = wget.download(dataurl,download_dir)
    print(f'downloaded at {wget_out_set}')
