import pandas as pd
import numpy as np
import os

input_dir=''
output_dir=''
print('loading data w sw and w/o msise (can take a few minutes)')
df_merged=pd.read_csv(os.path.join(input_dir,'satellites_data_w_sw_no_msise.csv'))
print('.. loaded')

df_nrlmsise00=pd.read_csv(os.path.join(input_dir,'densities_msise.csv'))
df_merged['NRLMSISE00__thermospheric_density__[kg/m**3]']=df_nrlmsise00.values.flatten()
df_merged.reset_index(drop=True,inplace=True)
df_merged.sort_values(by='all__dates_datetime__', inplace=True)
print('msise merged to data, let s save it to csv -> satellites_data_w_sw.csv')
df_merged.to_csv(os.path.join(output_dir,'satellites_data_w_sw.csv'),index=False)
print('done')

#subset of 1% of the data (taken randomly):
print('let s now subsample the dataset to 1% (randomly)')
sampled_values = df_merged.sample(frac=0.01, random_state=1)
sampled_values.sort_values(by='all__dates_datetime__', inplace=True)
sampled_values.reset_index(drop=True,inplace=True)
print('and save it')
sampled_values.to_csv(os.path.join(output_dir,'satellites_data_w_sw_2mln.csv'),index=False)

#description csv (useful for holding statistics about the data)
print('let s also store the summary statistics to csv')
df_describe=df_merged.describe()
df_describe.to_csv(os.path.join(output_dir,'satellites_data_w_sw_describe.csv'),index=False)
print('done')
