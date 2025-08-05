from multiprocessing import Pool

import argparse
import os
import pprint
import sys
import time
import datetime
import numpy as np
from functools import partial
from nrlmsise00 import msise_flat
import pandas as pd

os.environ['KMP_DUPLICATE_LIB_OK']='True'

def compute_density(inputs):
    date,  alt, latitude, longitude, f107A, f107, ap = inputs
    return msise_flat(date, alt, latitude, longitude, f107A, f107, ap)[:,5]*1e3

def create_dir(dir_path):
    if os.path.exists(dir_path):
        pass
    else:
        dir = os.makedirs(dir_path)

def create_groups(N, group_size=100):
    groups = []
    for i in range(0, N + 1, group_size):
        group = list(range(i, min(i + group_size, N )))
        groups.append(np.array(group))
    return groups

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise argparse.ArgumentTypeError('Not a valid date:' + s + '. Expecting YYYYMMDDHHMMSS.')

def main():
    parser = argparse.ArgumentParser(description='nrlmsise00 data',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--path_to_df', help='Path to dataframe', type=str, default = 'satellites_data_w_sw_no_msise.csv')
    parser.add_argument('--num_processes', help='Number of processes to be spawn', type=int, default = 32)
    parser.add_argument('--groups', help='Number of groups', type=int, default = 10000)
    opt = parser.parse_args()
    # File name to log console output
    db_dir='nrlmsise00_db'
    create_dir(db_dir)
    file_name_log = os.path.join(db_dir+'/nrlmsise00_db.log')
    te = open(file_name_log,'w')  # File where you need to keep the logs
    class Unbuffered:
        def __init__(self, stream):
            self.stream = stream

        def write(self, data):
            self.stream.write(data)
            self.stream.flush()
            te.write(data)    # Write the data of stdout here to a text file as well
            te.flush()

        def flush(self):
            self.stream.flush()
            te.flush()

    sys.stdout=Unbuffered(sys.stdout)

    print('Arguments:\n{}\n'.format(' '.join(sys.argv[1:])))
    print('Config:')
    pprint.pprint(vars(opt), depth=2, width=50)
    
    print('necessary loadings of the df:')
    df=pd.read_csv(opt.path_to_df)
    #df_describe=pd.read_csv('satellites_data_w_sw_describe.csv')
    dates=pd.to_datetime(df['all__dates_datetime__'].values)
    print('done')
    pool = Pool(processes=opt.num_processes)
    groups=create_groups(len(dates),10000)
    longitudes=df['tudelft_thermo__longitude__[deg]'].values#lon in deg
    latitudes=df['tudelft_thermo__latitude__[deg]'].values#lat in deg
    alts = df['tudelft_thermo__altitude__[m]'].values/1e3#alt in km
    f107= df['space_environment_technologies__f107_obs__'].values
    f107a=df['space_environment_technologies__f107_average__'].values
    ap=df['celestrack__ap_average__'].values
    
    print('inputs preparation:')
    inputs=[]
    for i in range(len(groups)):
        inputs.append((dates[groups[i]],  alts[groups[i]], latitudes[groups[i]], longitudes[groups[i]], f107a[groups[i]], f107[groups[i]], ap[groups[i]]))
    print(f'Starting parallel pool with {len(inputs)}:')
    print(f'example element: {inputs[0], inputs[-1]}')
    p = pool.map(compute_density, inputs)
    print('Done ... writing to file')

    densities=[]
    for input_data, result in zip(inputs, p):
        densities.append(result)
    #print(f'stacking {len(densities)}')
    densities=np.concatenate(densities)
    print(f'densities shape of array: {densities.shape}')
    df_densities=pd.DataFrame(densities)
    print('saving to csv')
    df_densities.to_csv(db_dir+'/densities_msise.csv',index=False)
    print('Done')

if __name__ == "__main__":
    time_start = time.time()
    main()
    print('\nTotal duration: {}'.format(time.time() - time_start))
    sys.exit(0)