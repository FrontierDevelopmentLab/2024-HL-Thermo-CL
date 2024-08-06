import functions_framework
from cloudevents.http import CloudEvent
from pathlib import Path
import zipfile
from karman.io import StorageClient
from karman.io import InfluxDBManager
import os
import time
import pandas as pd

# from karman.scripts.process_tudelft_thermo import process_one_swarm_file, process_one_champ_file, process_one_goce_file, process_one_grace_file
from process_tudelft_thermo import process_one_swarm_file, process_one_champ_file, process_one_goce_file, process_one_grace_file, process_satellite_data_columns, post_process_satellite_data
from merge_sw_and_satellites import post_process_merged_df

#  TODO: make more robust, are these keys correct?
function_map = {
    "CHAMP": process_one_champ_file,
    "SWARM": process_one_swarm_file,
    "GOCE": process_one_goce_file,
    "GRACE": process_one_grace_file
}

# TODO: make this more general, combine with satellite class?
def get_satellite_subtype(file_name, satellite) -> str:
    """
    GRACE and SWARM have a, b and c sub-types. 
    Decode this based on the filename
    """

    tokens = file_name.split("/")[-1].split("_")
    

    if satellite == "CHAMP":
        return "champ"
    elif satellite == "SWARM":
        {"SA": "swarm_a", "SB": "swarm_b", "SC": "swarm_c"}
        if tokens[0] in remap:
            return remap[tokens[0]]
        else:
            raise RuntimeError(f"Unrecognised SWARM satellite subtype in file {file_name}")
    elif satellite == "GOCE":
        return "goce"
    elif satellite == "GRACE":
        remap = {"GA": "grace_a", "GB": "grace_b", "GC": "grace_c"}
        if tokens[0] in remap:
            return remap[tokens[0]]
        else:
            raise RuntimeError(f"Unrecognised GRACE satellite subtype in file {file_name}")
    else:
        raise RuntimeError(f"Unregocnised satellite {satellite}")



def get_files_in_directory(directory):
    files = []
    try:
        # List all files and directories in the specified directory
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    files.append(entry.name)
    except FileNotFoundError:
        print(f"The directory {directory} does not exist.")
    except PermissionError:
        print(f"Permission denied to access {directory}.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return files


def unzip_file(zip_file_name, output_directory):
    with zipfile.ZipFile(zip_file_name, 'r') as zip_ref:
        zip_ref.extractall(output_directory)


def create_local_directories(input_file_name, prefix="/tmp"):
    local_file_name = f'{prefix}/{input_file_name}'
    local_directory_path = local_file_name.rsplit('/', 1)[0]
    # print(f"creating directory to store file: {local_directory_path}")
    Path(local_directory_path).mkdir(parents=True, exist_ok=True)
    return local_file_name

def get_indices_file_from_bucket(storage_client: StorageClient, local_directory: str) ->  pd.DataFrame:
    # Get the indices file
    indices_bucket = "sw-indices"
    indices_file = "processed/combined_indices.parquet"
    indices_local_file = f"{local_directory}/combined_indices.parquet"
    storage_client.download_file_from_bucket(
        source_bucket_name=indices_bucket,
        bucket_file_name=indices_file,
        local_file_name=indices_local_file
    )
    df_indices = pd.read_parquet(indices_local_file)
    return df_indices

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def triggered_on_file_landing_in_bucket(cloud_event: CloudEvent) -> tuple:
    """This function is triggered by a change in a storage bucket.

    Args:
        cloud_event: The CloudEvent that triggered this function.
    Returns:
        The event ID, event type, bucket, name, metageneration, and timeCreated.
    """

    #  hard-code for now
    output_bucket_name = "satellite-data-processed"

    data = cloud_event.data

    print(f"trig on land data recieved: {data}")

    # Extract data from the CloudEvent
    # event_id = cloud_event["id"]
    # event_type = cloud_event["type"]
    landing_bucket_name = data["bucket"]
    # metageneration = data["metageneration"]
    # timeCreated = data["timeCreated"]
    # updated = data["updated"]
    input_file_path = data["name"]  #  File that landed on the bucket

    print(f"File {input_file_path} landed on bucket {landing_bucket_name}")
    landing_file_base_path = input_file_path.rsplit('/', 1)[0]

    # Create a local directory to store the file
    local_file_name = create_local_directories(input_file_path)
    local_directory = Path(local_file_name).parent

    # Get the metadata associated with the file
    storage_client = StorageClient()
    metadata = storage_client.get_metadata_of_file(
        landing_bucket_name, input_file_path)
    print(metadata)
    satellite = metadata["satellite"]

    # Collect all files that are downloaded onto the local machine
    all_locally_downloaded_files = []

    #  zip file lands on bucket, copy from bucket to local
    storage_client.download_file_from_bucket(
        landing_bucket_name, input_file_path, local_file_name)

    pre_unzip_files = get_files_in_directory(local_directory)
    all_locally_downloaded_files += pre_unzip_files

    # unzip the file
    unzip_file(local_file_name, local_file_name.rsplit('/', 1)[0])

    post_unzip_files = get_files_in_directory(local_directory)

    # print what is in this directory
    print(f"Files in the directory {local_directory} after unzip are: {pre_unzip_files}")

    # get the files that were unzipped
    unzipped_files = list(set(post_unzip_files) - set(pre_unzip_files))
    all_locally_downloaded_files += unzipped_files

    # Get the indices data
    df_indices = get_indices_file_from_bucket(storage_client, local_directory)

    # # initialze the db manager
    # db_manager = InfluxDBManager()


    # Now process those unzipped files (there is likely only one)
    for file in unzipped_files:
        file_path = f"{local_directory}/{file}"

        satellite_subtype = get_satellite_subtype(file_path, satellite)

        print(f"Processing file: {file_path} ...")
        try:
            process_function = function_map[satellite]
        except KeyError:
            print(f"Satellite {satellite} not supported.")
            return

        # Process that dataframe
        df = process_function(file_path)
        df = process_satellite_data_columns(df=df, satellite_name=satellite_subtype)
        df = post_process_satellite_data(df)

        output_file_name = file.replace('txt', 'parquet')  #  assumes txt file...

        # # Upload the dataframe to the cloud
        # local_csv_file_name = f"{local_directory}/{output_file_name}"
        # remote_csv_file_name = f"{landing_file_base_path}/{output_file_name}"
        # df.to_csv(local_csv_file_name, index=False)

        # # upload this new CSV to the bucket
        # storage_client.upload_file_to_bucket(
        #     destination_bucket_name=output_bucket_name,
        #     source_file_name=local_csv_file_name,
        #     new_file_name=remote_csv_file_name,
        #     metadata={"satellite": satellite}
        # )

        # Make sure the time columns have the same precision
        df['all__dates_datetime__'] = df['all__dates_datetime__'].astype("datetime64[s]")
        df_indices['all__dates_datetime__'] = df_indices['all__dates_datetime__'].astype("datetime64[s]")


        # Join indices with the satellite data
        df_merged = pd.merge_asof(
            df,
            df_indices.copy(),
            on='all__dates_datetime__',
            direction='backward'
        )

        df_merged = post_process_merged_df(df_merged)

        df_merged = df_merged.drop_duplicates()

        # Store this local merged dataframe 
        local_merged_file_name = f"{local_directory}/{output_file_name}"
        df_merged.to_parquet(local_merged_file_name, index=False)


        all_locally_downloaded_files.append(local_merged_file_name)

        # Upload the merged file to the bucket
        remote_merged_file_name = f"{landing_file_base_path}/db_{output_file_name}"
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket_name,
            source_file_name=local_merged_file_name,
            new_file_name=remote_merged_file_name,
            metadata={"satellite": satellite}
        )

        # # Upload the data to influxdb
        # db_manager.upload_dataframe(df_merged)


    # Delete all files stored on this machine
    time.sleep(10)
    for file in all_locally_downloaded_files:
        os.remove(file)
