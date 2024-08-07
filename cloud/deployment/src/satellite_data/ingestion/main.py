import base64
import functions_framework
import json
import os
from karman.io import StorageClient

# from karman.scripts.download_tudelft_thermo import download_data
from download_tudelft_thermo import download_data


def get_satellite_subtype(file_name, satellite) -> str:
    """
    GRACE and SWARM have a, b and c sub-types. 
    Decode this based on the filename
    """

    tokens = file_name.split("/")[-1].split("_")
    
    if satellite == "CHAMP":
        return "champ"
    elif satellite == "SWARM":
        remap = {"SA": "swarm_a", "SB": "swarm_b", "SC": "swarm_c"}
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

@functions_framework.cloud_event
def hello_pubsub(cloud_event):

    # Print out the data from Pub/Sub, to prove that it worked
    print(f"Recieved the following message from pub/sub: {cloud_event.data}")

    message_data: str = base64.b64decode(cloud_event.data["message"]["data"])

    print(f"Extracted message data string: {message_data} with type {type(message_data)}")


    #  Load the input message
    try:
        message = json.loads(message_data)
    except json.JSONDecodeError as e:
        print(f"ERROR: unable to decode input message as json: {e}")
        return

    print(f"Extracted message data: {message} with type {type(message)}")
 
    project = message["project"]
    ftp_data_path = message["data_path"]
    output_bucket = message["bucket"]

    # Somewhere to store the data within this VM.
    local_base_dir = "/tmp/data"

    # Connect to cloud storage
    storage_client = StorageClient()

    #  Find what files exist on the bucket
    bucket_subdirectory = f"tudelft{ftp_data_path}/"
    existing_files = storage_client.list_files_in_bucket_directory(
        bucket_name=output_bucket,
        subdirectory=bucket_subdirectory
    )
    print(f"Found {len(existing_files)} files on bucket {output_bucket}/{bucket_subdirectory}, e.g. {existing_files[0:3]}")

    # strip to get what remains in the bucket subdir
    existing_files = [file.split("/")[-1] for file in existing_files]

    #  Download remaining files
    new_files = download_data(
        local_base_dir=local_base_dir,
        starting_ftp_directory=ftp_data_path,
        existing_files=existing_files
    )
    print(f"Downloaded {len(new_files)} files.")

    # Upload the new files to the bucket
    for local_file in new_files:

        local_file_ending = local_file.split("/")[-1]
        satellite_subtype = get_satellite_subtype(local_file_ending, project)
        
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket,
            source_file_name=f"{local_base_dir}/{local_file}",
            new_file_name=f"{bucket_subdirectory}{local_file.split('/')[-1]}",
            metadata={
                "project": project,
                "satellite": satellite_subtype
                }
        )
