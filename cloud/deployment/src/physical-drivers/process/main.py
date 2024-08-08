import functions_framework
from cloudevents.http import CloudEvent
from karman.io import StorageClient
from process_soho_data import process_soho_data
from process_omniweb import process_one_omniweb_file
import os
import time



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
    output_bucket_name = "physical-drivers-processed"

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
    file_name_ending = input_file_path.rsplit('/', 1)[-1]
    # landing_file_base_path = input_file_path.replace(f"{landing_bucket_name}/", "")
    print(file_name_ending)

    # Create a local directory to store the file
    local_storage_dir = "/tmp/soho_omniweb"
    os.makedirs(local_storage_dir, exist_ok=True)

    # download that file to the local machine
    local_file_name = f"{local_storage_dir}/{file_name_ending}"
    storage_client = StorageClient()
    metadata = storage_client.download_file_from_bucket(
        source_bucket_name=landing_bucket_name,
        bucket_file_name=input_file_path,
        local_file_name=local_file_name,
        debug=True
        )
    
    data_source = metadata["data_source"]

    if data_source == "SOHO":
        df = process_soho_data([local_file_name])
        local_output_file = local_file_name + ".parquet"
        bucket_output_file = input_file_path + ".parquet"
        df.to_parquet(local_output_file)

        # upload to the processed bucket
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket_name,
            source_file_name=local_output_file,
            new_file_name=bucket_output_file,
            metadata=metadata
        )

    elif data_source == "OMNIWEB":
        # Expects a per-month file with the structure "YYYY/data_YYYY_MM.txt"
        data_omni_magnetic_field, data_omni_solar_wind_velocity, data_omni_indices = process_one_omniweb_file(local_file_name) 

        year = file_name_ending.split("_")[1]
        month = file_name_ending.split("_")[2].split(".")[0]

        # Save these files as parquet
        magnetic_field_output_name = f"magnetic_field_omni_{year}_{month}.parquet"
        solar_wind_velocity_output_name = f"solar_wind_velocity_omni_{year}_{month}.parquet"
        indicies_output_name = f"indices_omni_{year}_{month}.parquet"

        data_omni_magnetic_field.to_parquet(f"{local_storage_dir}/{magnetic_field_output_name}")
        data_omni_solar_wind_velocity.to_parquet(f"{local_storage_dir}/{solar_wind_velocity_output_name}")
        data_omni_indices.to_parquet(f"{local_storage_dir}/{indicies_output_name}")


        # NOTE: there is a merge_omni.py script that merges these files into one
        # However at the moment, the dataload appears to consume these files separately.

        # Upload these data files to the bucket
        metadata["info"] = "magnetic_field"
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket_name,
            source_file_name=f"{local_storage_dir}/{magnetic_field_output_name}",
            new_file_name=f"OMNIWEB/{year}/{magnetic_field_output_name}",
            metadata=metadata
        )

        metadata["info"] = "solar_wind_velocity"
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket_name,
            source_file_name=f"{local_storage_dir}/{solar_wind_velocity_output_name}",
            new_file_name=f"OMNIWEB/{year}/{solar_wind_velocity_output_name}",
            metadata=metadata
        )

        metadata["info"] = "indices"
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket_name,
            source_file_name=f"{local_storage_dir}/{indicies_output_name}",
            new_file_name=f"OMNIWEB/{year}/{indicies_output_name}",
            metadata=metadata
        )
    
    # Remove the downloaded local file
    time.sleep(10)
    os.remove(local_file_name)
