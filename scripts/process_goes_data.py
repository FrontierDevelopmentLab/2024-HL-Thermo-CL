import netCDF4 as nc
import numpy as np
import cftime
import pandas as pd
import datetime
import os

# class GoesData:

#     def __init__(self, input_dir, output_dir):
#         self.input_dir = input_dir
#         self.output_dir = output_dir
#         self.wavelengths = [25.6, 28.4, 30.4, 117.5, 121.6, 133.5, 140.5]  # nm




def get_goes_data(input_dir: str, mission: int, year: int, str_irr, str_irr_flag):

    # file_path = input_dir+'/goes'+str(mission)+'/y'+str(year)+'.nc'
    if os.environ.get("is_local") == "True":
        file_path = f"{input_dir}/{year}/goes{mission}_y{year}.nc" 
    else:
        file_path = f"{input_dir}/goes{mission}_y{year}.nc" # file path for the cloud function

    print(f"Reading file: {file_path}")
    goes_ds = nc.Dataset(file_path)
    time_ds = goes_ds.variables['time']
    t = cftime.num2pydate(time_ds[:],time_ds.units)
    irr = goes_ds[str_irr][:]
    firr = goes_ds[str_irr_flag][:]

    return t, irr, firr


def get_str_irr(mission,wavelength):
    if mission < 16:
        if wavelength==30.4:
            str_irr = 'irr_chanB'
        elif wavelength==121.6:
            str_irr = 'irr_chanE_uncorr'
        str_irr_flag = 'irr_'+str(int(wavelength*10))+'_flag'
    else:
        str_irr = 'irr_'+str(int(wavelength*10))
        str_irr_flag = 'irr_'+str(int(wavelength*10))+'_flag'

    return str_irr,str_irr_flag



def get_missions_years(wavelength):

    this_year = datetime.datetime.now().year

    if wavelength==30.4 or wavelength==121.6:
        all_years = range(2010, this_year+1)
        # missions_years = [[15], [15], [15], [15], [15], [15], [15], [16, 15], [16, 17, 15], [16, 17, 15], [16, 17, 15], [16, 17], [16, 17, 18], [16, 17, 18], [16, 18]]
        missions_years = {
            2010: [15],
            2011: [15],
            2012: [15],
            2013: [15],
            2014: [15],
            2015: [15],
            2016: [15],
            2017: [16, 15],
            2018: [16, 17, 15],
            2019: [16, 17, 15],
            2020: [16, 17, 15],
            2021: [16, 17],
            2022: [16, 17, 18],
            2023: [16, 17, 18],
            2024: [16, 18]
        }
    else:
        all_years =range(2017, this_year+1)
        # missions_years = [[16], [16, 17], [16, 17], [16, 17], [16, 17], [16, 17, 18], [16, 17, 18], [16, 18]]
        missions_years = {
            2017: [16],
            2018: [16, 17],
            2019: [16, 17],
            2020: [16, 17],
            2021: [16, 17],
            2022: [16, 17, 18],
            2023: [16, 17, 18],
            2024: [16, 18]
        }
       
    # This code was written in 2024, at the time, only GOES 16 and 18 were operational. If this changes this code will need modifying 
    for yy in range(2024, this_year+1):
        missions_years[yy] = [16, 18]
    
    return missions_years, all_years
 
def process_one_wavelength_one_year(input_dir: str, wavelength: str, year: int) -> pd.DataFrame:

    print(f'Processing GOES irradiance data at {wavelength}nm for year {year}')

    strIrradiance = 'goes__irradiance_'+str(int(wavelength*10))+'nm___[W/m2]'
    strFlag = 'source__gaps_flag__'#'goes__irradiance_'+str(int(wavelength*10))+'nm___flag'

    dict_set = {
        'all__dates_datetime__': [],
        strIrradiance: [],
        strFlag: []
    }    

    dict_set = _process_dict_one_wavelength_one_year(
        year,
        wavelength,
        input_dir,
        dict_set,
    )

    try:
        first_index = list(x > 0 for x in dict_set[strIrradiance]).index(True)
    except ValueError:
        raise ValueError(f"No data for year {year}")

    # WJF: intended to stop processing data for the current year at the current time
    if year == datetime.datetime.now().year:
        last_index = list(x > datetime.datetime.now() for x in dict_set['all__dates_datetime__']).index(True)
    else:
        last_index = len(dict_set['all__dates_datetime__']) - 1 # This will return the save as the above, I think, but the above may miss out the very last date?! 

    dict_set['all__dates_datetime__'] = dict_set['all__dates_datetime__'][first_index:last_index]
    dict_set[strIrradiance] = dict_set[strIrradiance][first_index:last_index]
    dict_set[strFlag] = dict_set[strFlag][first_index:last_index]

    df_goes=pd.DataFrame(dict_set)
    df_goes.sort_values(by=['all__dates_datetime__'],ascending=True,inplace=True)
    return df_goes

def process_one_wavelength_all_years(input_dir, wavelength) -> pd.DataFrame:
    print(f'Processing GOES irradiance data at {wavelength}nm')

    strIrradiance = 'goes__irradiance_'+str(int(wavelength*10))+'nm___[W/m2]'
    strFlag = 'source__gaps_flag__'#'goes__irradiance_'+str(int(wavelength*10))+'nm___flag'


    dict_set = {
        'all__dates_datetime__': [],
        strIrradiance: [],
        strFlag: []
    }    


    missions_years, all_years = get_missions_years(wavelength)

    for year in all_years:
        dict_set = _process_dict_one_wavelength_one_year(
            year,
            wavelength,
            input_dir,
            dict_set,
            )
       

    first_index = list(x > 0 for x in dict_set[strIrradiance]).index(True)
    last_index = list(x > datetime.datetime.now() for x in dict_set['all__dates_datetime__']).index(True)

    dict_set['all__dates_datetime__'] = dict_set['all__dates_datetime__'][first_index:last_index]
    dict_set[strIrradiance] = dict_set[strIrradiance][first_index:last_index]
    dict_set[strFlag] = dict_set[strFlag][first_index:last_index]

    df_goes=pd.DataFrame(dict_set)
    df_goes.sort_values(by=['all__dates_datetime__'],ascending=True,inplace=True)
    return df_goes 


def _process_dict_one_wavelength_one_year(year: int, wavelength: int, input_dir: str, dict_set: dict) -> dict:

    prev_irradiance = -1
    prev_flag = 24*60

    missions_years, all_years = get_missions_years(wavelength)
    strIrradiance = 'goes__irradiance_'+str(int(wavelength*10))+'nm___[W/m2]'
    strFlag = 'source__gaps_flag__'#'goes__irradiance_'+str(int(wavelength*10))+'nm___flag'

    print(f'-----> Year {year}, wavelength {wavelength}nm')
    try:
        missions = missions_years[year]
    except KeyError:
        print(f'No data for year {year}')
        return dict_set



    all__dates = pd.date_range(start=datetime.datetime(year,1,1,0,0), end=datetime.datetime(year,12,31,23,59), freq="1min")
    num_dates = np.size(all__dates)
    
    num_missions = np.size(missions)

    goes__irradiance = -1*np.ones([num_dates,num_missions+1])
    goes__irradiance__flag = -1*np.ones([num_dates,num_missions+1])

    for imission in range(num_missions):
        str_irr,str_irr_flag = get_str_irr(missions[imission], wavelength)
        time_stamp, irr, firr = get_goes_data(input_dir, missions[imission], year, str_irr, str_irr_flag)

        istart = np.where(all__dates==time_stamp[0])[0][0]
        iend = np.where(all__dates==time_stamp[-1])[0][0]

        goes__irradiance[istart:iend+1,imission] = irr
        goes__irradiance__flag[istart:iend+1,imission] = firr

    for itime in range(num_dates):
        imission = 0
        irr_check = -1

        while imission<num_missions and irr_check<0:
            irr = goes__irradiance[itime,imission]

            if goes__irradiance__flag[itime,imission]==0:
                if not(missions[imission]<16 and num_missions>1):
                    goes__irradiance__flag[itime,-1] = 0
                    goes__irradiance[itime,-1] = irr

                    prev_irradiance = irr
                    prev_flag = 0

                    irr_check = 1

            imission +=1

        if irr_check<0:
            goes__irradiance[itime,-1] = prev_irradiance
            prev_flag += 1

            if prev_flag < 30:
                goes__irradiance__flag[itime] = 1
            elif prev_flag < 120:
                goes__irradiance__flag[itime] = 2
            elif prev_flag < 24*60:
                goes__irradiance__flag[itime] = 3
            else:
                goes__irradiance__flag[itime] = 4

    #Storage
    dict_set['all__dates_datetime__'].extend(all__dates)
    dict_set[strIrradiance].extend(goes__irradiance[:,-1])
    dict_set[strFlag].extend(goes__irradiance__flag[:,-1])

    return dict_set




def process_goes_data(input_dir, output_dir):
    """
    Adaptation of original function written by Jordi
    """

    all_wavelengths = [25.6, 28.4, 30.4, 117.5, 121.6, 133.5, 140.5]    #nm
    for wavelength in all_wavelengths:
        df_goes = process_one_wavelength_all_years(input_dir, wavelength)
        outputstr = 'goes_irradiance_'+str(int(wavelength*10))+'nm_sw.csv'
        df_goes.to_csv(os.path.join(output_dir, outputstr),index=False)


def process_all_wavelengths_one_year(input_dir: str, output_dir: str, year: int) -> list[str]:
    """
    Modified function to process a single year, used for the cloud function.
    """
    all_wavelengths = [25.6, 28.4, 30.4, 117.5, 121.6, 133.5, 140.5]    #nm
    output_files = []
    for wavelength in all_wavelengths:
        mission_years, _ = get_missions_years(wavelength)
        if year not in mission_years:
            print(f"Wavelength {wavelength}nm not available for year {year}, skipping")
            continue

        try:
            df_goes = process_one_wavelength_one_year(input_dir, wavelength, year)
            outputstr = f'goes_irradiance_{year}_{int(wavelength*10)}nm_sw.parquet'
            df_goes.to_parquet(os.path.join(output_dir, outputstr),index=False)
            output_files.append(outputstr)
        except ValueError as e:
            print(f"Error processing data for wavelength {wavelength}nm: {e}, no first_index found, assume no data for year {year}")
    return output_files

def main():
    os.environ["is_local"] = "True"
    input_dir = '/shared/raw/goes'
    input_dir = "/shared/raw/GOES"
    output_dir = '/shared/processed/goes'

    # process_goes_data(input_dir, output_dir)
    process_all_wavelengths_one_year(input_dir, output_dir, 2015)

if __name__ == "__main__":
    main()