import base64
import functions_framework
from karman.io import StorageClient
import os
import json
import time
from download_goes_irradiance_yearly import download_goes18, download_goes17, download_goes16, download_goes15, download_goes14


"""
This cloud function is used to download GOES data.
The function is triggered by a Pub/Sub message, which contains the following information:
- project: (the only acceptable value is GOES)
- bucket: the name of the bucket where the data will be stored
- satellite: the name of the satellite from which the data will be downloaded (this must be one of goes15, goes16, goes17, goes18)
- year: the year of data to download

Note, not all satellites have data for all years, for example, goes14 was not operational in 2011, but was in 2010 and 2012.

"""

function_map = {
    "goes_14": download_goes14, 
    "goes15": download_goes15,
    "goes16": download_goes16,
    "goes17": download_goes17,
    "goes18": download_goes18
}

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
 
    # Exttact the relevant information from the message
    project = message["project"]
    output_bucket = message["bucket"]
    satellite = message["satellite"]
    year = message["year"] # the year of data to download

    # Check the input values
    if project != "GOES":
        print(f"ERROR: invalid project name: {project}")
        return
    if satellite not in function_map.keys():
        print(f"ERROR: invalid satellite name: {satellite}")
        return

    # Download the data
    print(f"Will attempt to download data for {satellite} for year {year}...")
    local_output_directory = "/tmp/goes"
    os.makedirs(local_output_directory, exist_ok=True)
    downloaded_file = function_map[satellite](year, local_output_directory)

    # Not all satellites were active for all years, so the file may not exist. If so exit here. 
    if downloaded_file is None:
        print(f"Unable to download data for {satellite} for year {year}. It may not exist.")
        return
    print(f"Downloaded file: {downloaded_file}")

    # Add metadata to the file
    metadata = {
        "proejct": project,
        "satellite": satellite,
        "year": year,
    }

    # upload this file to the bucket
    storage_client = StorageClient()
    storage_client.upload_file_to_bucket(
        destination_bucket_name=output_bucket,
        source_file_name=downloaded_file,
        new_file_name=f"GOES/{year}/{satellite}_y{year}.nc",
        metadata=metadata,
        verbose=True
    )

    # delete the locally downloaded file
    # time.sleep(10)
    # os.remove(downloaded_file)
