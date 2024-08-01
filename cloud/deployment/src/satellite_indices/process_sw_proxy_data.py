import numpy as np
import os
import datetime
import pandas as pd


def get_sw_set(sw_data,t_mjd):
    """
    See: https://github.com/lcx366/ATMOS
    """

    sw_data1,sw_data2 = sw_data
    sw_mjd = sw_data1[:,0] - 2400000.5
    J_, = np.where(sw_mjd-0.5 < t_mjd)
    j = J_[-1]

    # USE 1 DAY LAG FOR F10 AND S10 FOR JB2008
    dlag = j-1
    F10,F10B,S10,S10B = sw_data1[dlag,1:5] 

    # USE 2 DAY LAG FOR M10 FOR JB2008
    dlag = j-2
    M10,M10B = sw_data1[dlag,5:7] 

    # USE 5 DAY LAG FOR Y10 FOR JB2008
    dlag = j-5
    Y10,Y10B = sw_data1[dlag,7:9] 
    
    t_dmjd = t_mjd - sw_mjd[j] + 0.5
    x = np.arange(0.5,48)/24
    y = sw_data2[j:j+2].flatten()
    DTCVAL = np.interp(t_dmjd,x,y)          
    return F10,F10B,S10,S10B,M10,M10B,Y10,Y10B,DTCVAL


def jd_to_datetime(jd):    
    JD_GREGORIAN_EPOCH = 1721425.5
    
    days_since_epoch = jd - JD_GREGORIAN_EPOCH
    
    epoch = datetime.datetime(1, 1, 1)  # January 1, 1 AD
    date = epoch + datetime.timedelta(days=days_since_epoch)
    
    return date


def get_sw_celestrack(sw_df,t_ymd):
    j_, = np.where(sw_df['DATE'] == t_ymd)
    j = j_[0]
    f107A,f107,ap = sw_df.iloc[j]['F10.7_OBS_CENTER81'],sw_df.iloc[j+1]['F10.7_OBS'],sw_df.iloc[j]['AP_AVG']
    return f107A,f107,ap


def process_sw_data(sw_data1, sw_data2) -> pd.DataFrame:
    print("Processing SET data...")
    swdata=(sw_data1, sw_data2)

    dict_set={"all__dates_datetime__":[],
          "space_environment_technologies__f107_obs__":[],
          "space_environment_technologies__f107_average__":[],
          "space_environment_technologies__s107_obs__":[],
          "space_environment_technologies__s107_average__":[],
          "space_environment_technologies__m107_obs__":[],
          "space_environment_technologies__m107_average__":[],
          "space_environment_technologies__y107_obs__":[],
          "space_environment_technologies__y107_average__":[],
          "JB08__d_st_dt__[K]":[]}

    dates=[]
    for i in range(len(sw_data1)-1):
        date=jd_to_datetime(sw_data1[i,0]).strftime('%Y-%m-%d')
        t_mjd=sw_data1[i,0] - 2400000.5
        f107_obs,f107_avg,s107_obs,s107_avg,m107_obs,m107_avg,y107_obs,y107_avg,dDst_dt=get_sw_set(swdata,t_mjd)
        dict_set['all__dates_datetime__'].append(date)
        dict_set['space_environment_technologies__f107_obs__'].append(f107_obs)
        dict_set['space_environment_technologies__f107_average__'].append(f107_avg)
        dict_set['space_environment_technologies__s107_obs__'].append(s107_obs)
        dict_set['space_environment_technologies__s107_average__'].append(s107_avg)
        dict_set['space_environment_technologies__m107_obs__'].append(m107_obs)
        dict_set['space_environment_technologies__m107_average__'].append(m107_avg)
        dict_set['space_environment_technologies__y107_obs__'].append(y107_obs)
        dict_set['space_environment_technologies__y107_average__'].append(y107_avg)
        dict_set['JB08__d_st_dt__[K]'].append(dDst_dt)

    df = pd.DataFrame(dict_set)
    return df


def process_celestrack_data(sw_df) -> pd.DataFrame:
    print("Processing Celestrack data...")
    dict_celestrack={"all__dates_datetime__" :[],
                    "celestrack__ap_average__":[]}
    dates=sw_df['DATE'].values
    for i in range(len(sw_df['DATE'].values)-1):    
        _,_,ap=get_sw_celestrack(sw_df,dates[i])
        dict_celestrack['all__dates_datetime__'].append(dates[i])
        dict_celestrack['celestrack__ap_average__'].append(ap)
    #save it as pandas csv
    df_celestrack=pd.DataFrame(dict_celestrack)
    df_celestrack.sort_values(by=['all__dates_datetime__'],ascending=True,inplace=True)
    return df_celestrack


def process_sw_proxy_data(input_dir: str, output_dir: str) -> list[str]:
    """
    Process the SW data and save it to the output directory.
    Returns:
        - list of the output files:
        - [set_output, celestrack_output]
    """


    #first let's take care of the SET data (F10.7, S10.7, M10.7, Y10.7, dDst/dT)
    sw_data1 = np.loadtxt(os.path.join(input_dir,'SOLFSMY.TXT'),usecols=range(2,11))
    sw_data2 = np.loadtxt(os.path.join(input_dir,'DTCFILE.TXT'),usecols=range(3,27),dtype=int)

    sw_df = process_sw_data(sw_data1, sw_data2)
    set_output = os.path.join(output_dir,'set_sw.csv')
    print(f"Saving to {set_output}")
    sw_df.to_csv(set_output, index=False)

    ######### Now let's take care of the Celestrack data
    sw_df = pd.read_csv(os.path.join(input_dir,'SW-All.csv'))
    df_celestrack = process_celestrack_data(sw_df)
    celestrack_output = os.path.join(output_dir,'celestrack_sw.csv')
    print(f"Saving to {celestrack_output}")
    df_celestrack.to_csv(celestrack_output,index=False)

    return [set_output, celestrack_output]


def main():

    input_dir = '/home/willfaw/data/raw/indices'
    output_dir = '/home/willfaw/data/processed'

    processed_results = process_sw_proxy_data(input_dir, output_dir)


if __name__ == "__main__":
    main()