from multiprocessing import Pool

import argparse
import os
import pprint
import sys
import time
import numpy as np
import pandas as pd

from nrlmsise00_general import compute_density, create_groups

os.environ['KMP_DUPLICATE_LIB_OK']='True'



def main(processes: int, path_to_df: str, n_groups: int, debug: bool):

    from nrlmsise00_general import Unbuffered


    # File name to log console output
    db_dir='nrlmsise00_db'


    os.makedirs(db_dir)
    file_name_log = os.path.join(db_dir+'/nrlmsise00_db.log')
    te = open(file_name_log,'w')  # File where you need to keep the logs
    sys.stdout=Unbuffered(sys.stdout, te)

    
    # Open the file
    if path_to_df.endswith('.csv'):
        df=pd.read_csv(path_to_df)
    elif path_to_df.endswith('.parquet'):
        df=pd.read_parquet(path_to_df)
    else:
        raise ValueError('File format not supported')

    df_densities=create_nrlmsise00(df, processes, n_groups, debug)

    print('saving to csv')
    output_file = db_dir+'/densities_msise.csv'
    print(output_file)
    df_densities.to_csv(output_file,index=False)
    print('Done')

def create_nrlmsise00(df: pd.DataFrame, processes: int, n_groups: int, debug=False):
    """
    Args:
        df: pandas DataFrame -- satellite data without NRLMSISE00 data
        processes: number of processes to spawn
        n_groups: number of groups
    """

    dates=pd.to_datetime(df['all__dates_datetime__'].values)
    pool = Pool(processes=processes)
    groups=create_groups(len(dates), n_groups)
    longitudes=df['tudelft_thermo__longitude__[deg]'].values#lon in deg
    latitudes=df['tudelft_thermo__latitude__[deg]'].values#lat in deg
    alts = df['tudelft_thermo__altitude__[m]'].values/1e3#alt in km
    f107= df['space_environment_technologies__f107_obs__'].values
    f107a=df['space_environment_technologies__f107_average__'].values
    ap=df['celestrack__ap_average__'].values
    
    if debug:
        print('inputs preparation:')
    inputs=[]
    for i in range(len(groups)):
        inputs.append((dates[groups[i]],  alts[groups[i]], latitudes[groups[i]], longitudes[groups[i]], f107a[groups[i]], f107[groups[i]], ap[groups[i]]))
    if debug:
        print(f'Starting parallel pool with {len(inputs)}:')
        print(f'example element: {inputs[0], inputs[-1]}')
    p = pool.map(compute_density, inputs)
    if debug:
        print('Done ... writing to file')

    densities=[]
    for input_data, result in zip(inputs, p):
        densities.append(result)
    #print(f'stacking {len(densities)}')
    densities=np.concatenate(densities)
    if debug:
        print(f'densities shape of array: {densities.shape}')
    df_densities=pd.DataFrame(densities)

    return df_densities


if __name__ == "__main__":

    time_start = time.time()
    parser = argparse.ArgumentParser(description='nrlmsise00 data',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--path_to_df', help='Path to dataframe', type=str, default = 'satellites_data_w_sw_no_msise.csv')
    parser.add_argument('--num_processes', help='Number of processes to be spawn', type=int, default = 32)
    parser.add_argument('--groups', help='Number of groups', type=int, default = 10000)
    parser.add_argument('--debug', help='Debug mode', action='store_true', default=False)
    opt = parser.parse_args()

    print('Arguments:\n{}\n'.format(' '.join(sys.argv[1:])))
    print('Config:')
    pprint.pprint(vars(opt), depth=2, width=50)

    processes = opt.num_processes
    path_to_df = opt.path_to_df
    groups = opt.groups
    debug = opt.debug

    main(processes, path_to_df, groups, debug)
    print('\nTotal duration: {}'.format(time.time() - time_start))
    sys.exit(0)
