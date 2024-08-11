import base64
import functions_framework
from karman.io import StorageClient
import os
import json
import time
from datetime import datetime


"""
This cloud function is used to process GOES data. This function is triggered by a Pub/Sub message, which contains the following information:
{"project": "GOES",  "output_bucket": "satellite-data-processed", "year": 2011}   

Note the year field is optional, and if nothing is provided, the current year is used.
"""

from process_goes_data import process_all_wavelengths_one_year


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
 
    # Extract the relevant information from the message
    project = message["project"]
    output_bucket = message["output_bucket"] # the bucket to upload the processed data to
    input_data_bucket = "satellite-data-landing" # hard coded, could be passed via message

    try:
        year = int(message["year"]) # the year of data to download
    except KeyError:
        year = datetime.now().year


    # Create a local directory to store the data
    local_storage_dir = f"/tmp/GOES/{year}"
    os.makedirs(local_storage_dir, exist_ok=True)


    # Download the GOES data for this year
    storage_client = StorageClient()
    files_on_bucket = storage_client.list_files_in_bucket_directory(input_data_bucket, f"GOES/{year}")
    print(f"Found the following files for year {year}: {files_on_bucket}")
    locally_downloaded_files = []
    for file in files_on_bucket:
        print(f"Downloading file {file} to {local_storage_dir}")
        local_file_name = f"{local_storage_dir}/{file.split('/')[-1]}"
        storage_client.download_file_from_bucket(
            source_bucket_name=input_data_bucket,
            bucket_file_name=file,
            local_file_name=local_file_name
        )
        locally_downloaded_files.append(local_file_name)


    # Process the GOES data from the specified year
    print(f"Processing GOES data for year {year}")
    output_files = process_all_wavelengths_one_year(local_storage_dir, local_storage_dir, year)

    # Upload the processed data to the output bucket
    for output_file in output_files:
        print(f"Uploading file {output_file}")
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket, 
            source_file_name=f"{local_storage_dir}/{output_file}",
            new_file_name=f"GOES/{year}/{output_file}",
            metadata={"year": year, "project": project, "updated": time.time()}
            )
        
    # remove the local storage directory
    for file in locally_downloaded_files:
        os.remove(file)
