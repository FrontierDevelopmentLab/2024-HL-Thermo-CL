import os
import wget


def main():
    output_dir = '/shared/raw/goes'
    if not os.path.isdir(output_dir+'goes'):
        os.mkdir(output_dir+'goes')
    download_goes(output_dir)


def download_goes(output_dir):

    url1 = 'https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/euvs/'
    url2 = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/'

    download_finished_missions(output_dir, url1, url2)
    download_active_missions(output_dir, url2)


def download_active_missions(output_dir, url2):


    from datetime import datetime
    this_year = datetime.now().year
    y16 = list(range(2017,this_year+1))
    y18 = list(range(2022,this_year+1))

    download_goes16(y16, output_dir, url2)
    download_goes18(y18, output_dir, url2)
    

def download_finished_missions(output_dir, url1, url2):
    
    # These missions (14, 15 and 17) are now finished. 
    y14 = [2009, 2010, 2012, 2015, 2016, 2017, 2018, 2019, 2020]
    y15 = list(range(2010,2020+1))
    y17 = list(range(2018,2023+1))

    download_goes14(y14=y14, output_dir=output_dir, url1=url1)
    download_goes15(y15=y15, output_dir=output_dir, url1=url1)
    download_goes17(y17=y17, output_dir=output_dir, url2=url2)


def download_goes14(y14, output_dir, url1):
    #GOES 14 (not operational in 2024)
    for year in y14:
        dataurl = url1 + 'goes14' + '/geuv-l2-avg1m/sci_geuv-l2-avg1m_g14_y' + str(year) + '_v5-0-0.nc'
        download_dir = output_dir + 'goes/goes14_y' + str(year) + '.nc'
        wget_out_set = wget.download(dataurl,download_dir)
        print(f'downloaded at {wget_out_set}')

def download_goes15(y15, output_dir, url1):
    #GOES 15 (not operational in 2024)
    for year in y15:
        dataurl = url1 + 'goes15' + '/geuv-l2-avg1m/sci_geuv-l2-avg1m_g15_y' + str(year) + '_v5-0-0.nc'
        download_dir = output_dir + 'goes/goes15_y' + str(year) + '.nc'
        wget_out_set = wget.download(dataurl,download_dir)
        print(f'downloaded at {wget_out_set}')

def download_goes16(y16, output_dir, url2):
    #GOES 16 (operational in 2024)
    for year in y16:
        dataurl = url2 + 'goes16' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g16_y' + str(year) + '_v1-0-4.nc'
        download_dir = output_dir + 'goes/goes16_y' + str(year) + '.nc'
        wget_out_set = wget.download(dataurl,download_dir)
        print(f'downloaded at {wget_out_set}')


def download_goes17(y17, output_dir, url2):
    #GOES 17 (not operational in 2024)
    for year in y17:
        dataurl = url2 + 'goes17' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g17_y' + str(year) + '_v1-0-4.nc'
        download_dir = output_dir + 'goes/goes17_y' + str(year) + '.nc'
        wget_out_set = wget.download(dataurl,download_dir)
        print(f'downloaded at {wget_out_set}')



def download_goes18(y18, output_dir, url2):
    #GOES 18 (operational in 2024)
    for year in y18:
        dataurl = url2 + 'goes18' + '/l2/data/euvs-l2-avg1m_science/sci_euvs-l2-avg1m_g18_y' + str(year) + '_v1-0-4.nc'
        download_dir = output_dir + 'goes/goes18_y' + str(year) + '.nc'
        wget_out_set = wget.download(dataurl,download_dir)
        print(f'downloaded at {wget_out_set}')


if __name__ == "__main__":
    main()