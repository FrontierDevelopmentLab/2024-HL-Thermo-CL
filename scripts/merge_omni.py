import pandas as pd
import os
from tqdm import tqdm

base_path='../data/omniweb_data'
filenames=os.listdir(base_path)
filenames_magnetic_field=[os.path.join(base_path,f) for f in filenames if f.endswith('.csv') and f.startswith('magnetic_field')]
filenames_solar_wind=[os.path.join(base_path,f) for f in filenames if f.endswith('.csv') and f.startswith('solar_wind')]
filenames_indices=[os.path.join(base_path,f) for f in filenames if f.endswith('.csv') and f.startswith('indices')]

def create_df(filenames):
    dataframes = []
    for filename in tqdm(filenames):
        df = pd.read_csv(filename)
        dataframes.append(df)
    final_dataframe = pd.concat(dataframes, ignore_index=True)
    return final_dataframe

final_df_magnetic_field=create_df(filenames_magnetic_field)
final_df_magnetic_field.sort_values('all__dates_datetime__',inplace=True)
file_path=os.path.join(base_path,'merged_omni_magnetic_field.csv')
final_df_magnetic_field.to_csv(file_path,index=False)
print(f' OMNI magnetic field merged dataframe created at: {file_path}')
del final_df_magnetic_field

final_df_solar_wind=create_df(filenames_solar_wind)
final_df_solar_wind.sort_values('all__dates_datetime__',inplace=True)
file_path=os.path.join(base_path,'merged_omni_solar_wind.csv')
final_df_solar_wind.to_csv(file_path,index=False)
print(f' OMNI Solar Wind merged dataframe created at: {file_path}')
del final_df_solar_wind


final_df_indices=create_df(filenames_indices)
final_df_indices.sort_values('all__dates_datetime__',inplace=True)
file_path=os.path.join(base_path,'merged_omni_indices.csv')
final_df_indices.to_csv(file_path,index=False)
print(f' OMNI Indices merged dataframe created at: {file_path}')
del final_df_indices

