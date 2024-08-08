from multiprocessing import Pool

import argparse
import os
import pprint
import sys
import time
import numpy as np
from functools import partial
import pandas as pd

from nrlmsise00_general import compute_density, create_groups, Unbuffered

os.environ['KMP_DUPLICATE_LIB_OK']='True'


def main():
    parser = argparse.ArgumentParser(description='nrlmsise00 data',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--date_start', help='Start date', type=str, default ="2000-01-01 12:00:00")
    parser.add_argument('--date_end', help='End date', type=str, default ="2024-06-30 23:59:00")
    parser.add_argument('--num_processes', help='Number of processes to be spawn', type=int, default = 32)
    parser.add_argument('--groups', help='Number of groups', type=int, default = 50000)
    opt = parser.parse_args()
    # File name to log console output
    db_dir='nrlmsise_db_time_series'
    os.makedirs(db_dir)
    file_name_log = os.path.join(db_dir+'/nrlmsise00_db_time_series.log')
    te = open(file_name_log,'w')  # File where you need to keep the logs


    sys.stdout=Unbuffered(sys.stdout, te)

    print('Arguments:\n{}\n'.format(' '.join(sys.argv[1:])))
    print('Config:')
    pprint.pprint(vars(opt), depth=2, width=50)
    
    pool = Pool(processes=opt.num_processes)
    date_start=pd.to_datetime(opt.date_start)
    date_end=pd.to_datetime(opt.date_end)
    dates = pd.date_range(start=date_start, end=date_end, freq='1T')
    dates=np.repeat(dates,10)
    groups=create_groups(len(dates),opt.groups)
    
    alts=np.tile([350.]*10,int(len(dates)/10))
    #10 hardcoded lat/lon pairs (from Fibonacci sphere)
    lat_lon_points=[(90.0, 0.0), 
                    (51.057558731018624, 137.50776405003785), 
                    (33.74898859588859, -84.98447189992432), 
                    (19.471220634490695, 52.5232921501135), 
                    (6.379370208442807, -169.96894379984863), 
                    (-6.379370208442807, -32.461179749810775), 
                    (-19.471220634490688, 105.046584300227), 
                    (-33.74898859588859, -117.44565164973505), 
                    (-51.05755873101861, 20.062112400302713), 
                    (-90.0, 180.0)]
    latitudes=[x[0] for x in lat_lon_points]
    longitudes=[x[1] for x in lat_lon_points]
    latitudes=np.tile(latitudes,int(len(dates)/10))
    longitudes=np.tile(longitudes,int(len(dates)/10))
    f107=np.tile([88.]*10,int(len(dates)/10))
    f107a=np.tile([88.]*10,int(len(dates)/10))
    ap=np.tile([6.]*10,int(len(dates)/10))    
    print('inputs preparation:')
    inputs=[]
    for i in range(len(groups)):
        inputs.append((dates[groups[i]],  alts[groups[i]], latitudes[groups[i]], longitudes[groups[i]], f107a[groups[i]], f107[groups[i]], ap[groups[i]]))
    print(f'Starting parallel pool with {len(inputs)}:')
    print(f'example element: {inputs[0], inputs[-1]}')
    p = pool.map(compute_density, inputs)
    print('Done ... writing to file')

    densities=[]
    for _, result in zip(inputs, p):
        densities.append(result)
    #print(f'stacking {len(densities)}')
    densities=np.concatenate(densities)
    print(f'densities shape of array: {densities.shape}')
    densities=densities.reshape(-1,10)
    cols=[f'lat_{latitudes[:10][i]:.1f}_lon_{longitudes[:10][i]:.1f}' for i in range(10)]
    cols=['nrlmsise00__'+el+'__[kg/m**3]' for el in cols]
    df_densities=pd.DataFrame(densities,columns=cols)
    df_densities['all__dates_datetime__']=pd.to_datetime(dates.values.reshape(-1,10)[:,0])
    
    print('saving to csv')
    df_densities.to_csv(db_dir+'/nrlmsise00_time_series.csv',index=False)
    print('Done')

if __name__ == "__main__":
    time_start = time.time()
    main()
    print('\nTotal duration: {}'.format(time.time() - time_start))
    sys.exit(0)