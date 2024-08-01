import pandas as pd
import os
import numpy as np

input_dir=''
df=pd.read_csv(os.path.join(input_dir,'satellites_data.csv'))
dates=pd.DatetimeIndex(df['all__dates_datetime__'].values)
df['all__dates_datetime__']=dates

#celestrack sw data:
celestrack_sw=pd.read_csv(os.path.join(input_dir,'celestrack_sw.csv'))
celestrack_sw['all__dates_datetime__']=pd.DatetimeIndex(celestrack_sw['all__dates_datetime__'])
celestrack_sw.sort_values(by='all__dates_datetime__', inplace=True)
#now the SET ones
set_sw=pd.read_csv(os.path.join(input_dir,'set_sw.csv'))
set_sw['all__dates_datetime__']=pd.DatetimeIndex(set_sw['all__dates_datetime__'])
set_sw.sort_values(by='all__dates_datetime__', inplace=True)

sw_data = pd.merge_asof(celestrack_sw,
                              set_sw, 
                              on='all__dates_datetime__', 
                              direction='backward')

df_merged = pd.merge_asof(df,
                          sw_data, 
                          on='all__dates_datetime__', 
                          direction='backward')
del df

to_drop=[]
for col in df_merged.columns:
    if col.startswith('Unn'):
        to_drop.append(col)
if len(to_drop)>0:
    df_merged.drop(to_drop,axis=1,inplace=True)
    
df_merged.replace([np.inf, -np.inf], np.nan,inplace=True)
df_merged.dropna(axis=0,inplace=True)
df_merged.reset_index(drop=True,inplace=True)
df_merged.sort_values(by='all__dates_datetime__', inplace=True)
df_merged.reset_index(drop=True,inplace=True)
#now let's also add msise density data as an extra column:
df_merged.to_csv(input_dir+'satellites_data_w_sw_no_msise.csv',index=False)