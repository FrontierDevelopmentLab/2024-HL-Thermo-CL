import functions_framework
from cloudevents.http import CloudEvent
from pathlib import Path
import zipfile
from karman.io import StorageClient
from karman.io import InfluxDBManager
import os
import pandas as pd




def create_local_directories(input_file_name, prefix="/tmp"):
    local_file_name = f'{prefix}/{input_file_name}'
    local_directory_path = local_file_name.rsplit('/', 1)[0]
    # print(f"creating directory to store file: {local_directory_path}")
    Path(local_directory_path).mkdir(parents=True, exist_ok=True)
    return local_file_name


# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def triggered_on_file_landing_in_bucket(cloud_event: CloudEvent) -> tuple:
    """This function is triggered by a change in a storage bucket.

    Args:
        cloud_event: The CloudEvent that triggered this function.
    Returns:
        The event ID, event type, bucket, name, metageneration, and timeCreated.
    """


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


    #  File lands on bucket, copy from bucket to local
    storage_client = StorageClient()
    storage_client.download_file_from_bucket(
        landing_bucket_name, input_file_path, local_file_name, debug=True)
    
    # read the dataframe

    df = pd.read_csv(local_file_name)

    # initialze the db manager
    db_manager = InfluxDBManager()

    # Upload the data to influxdb
    db_manager.upload_dataframe(df)
