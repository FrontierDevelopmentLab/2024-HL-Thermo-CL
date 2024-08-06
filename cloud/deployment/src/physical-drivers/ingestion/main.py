import base64
import functions_framework
import json
import os
from karman.io import StorageClient
from glob import glob

from download_soho import SohoDownloader, get_all_years
from download_omniweb import download_omniweb_data_one_year


@functions_framework.cloud_event
def hello_pubsub(cloud_event):

    # Print out the data from Pub/Sub, to prove that it worked
    print(f"Recieved the following message from pub/sub: {cloud_event.data}")
    message_data: str = base64.b64decode(cloud_event.data["message"]["data"])
    print(f"Extracted message data string: {
          message_data} with type {type(message_data)}")

    output_bucket = "physical-drivers-landing"

    #  Load the input message
    try:
        message = json.loads(message_data)
    except json.JSONDecodeError as e:
        print(f"ERROR: unable to decode input message as json: {e}")
        return
    print(f"Extracted message data: {message} with type {type(message)}")

    # Extract the data source (expect either SOHO or OMNIWEB)
    data_source = message["data_source"]
    if data_source == "SOHO":
        ingest_soho(output_bucket)
    elif data_source == "OMNIWEB":
        ingest_omniweb(output_bucket)
    else:
        raise ValueError(f"Unknown data source: {data_source}")


def ingest_omniweb(output_bucket):

    this_year = get_all_years()[-1]

    output_dir = "/shared/raw/omniweb"
    downloaded_file = download_omniweb_data_one_year(this_year, output_dir)
    downloaded_files = [downloaded_file]
    print(downloaded_files)

    # Note, we *don't* want to check that if the files have already been uploaded or not.
    # The <this year> file will be updated every day, so we want to upload it every day.

    # Want to upload these files to the cloud with the file paths: OMNIWEB/FILE
    storage_client = StorageClient()
    for local_file in downloaded_files:
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket,
            source_file_name=local_file,
            new_file_name=f"OMNIWEB/{local_file.split('/')[-1]}",
            metadata={
                "data_source": "OMNIWEB",
                "satellite": "OMNIWEB"
                }
        )

    

def ingest_soho(output_bucket):

    """
    Will download the latest year's SOHO data to the local machine, and then upload those files to the cloud.
    """

    # Get the years to download, we probably only ever want the most recent data
    this_year = get_all_years()[-1]

    output_dir = "/shared/raw/soho"

    downloader = SohoDownloader(output_dir)
    downloader.download_data_parallel([this_year])

    #  find all the files that have been downloaded
    downloaded_files = glob(f"{output_dir}/{this_year}/*")

    # remove any "robots" file
    downloaded_soho_files = [x for x in downloaded_files if "robots" not in x]
    print(f"Downloaded {len(downloaded_soho_files)} files.")

    # Check what files have been already uploaded to the cloud
    storage_client = StorageClient()
    bucket_subdirectory = f"SOHO/{this_year}/"
    existing_files = storage_client.list_files_in_bucket_directory(
        bucket_name=output_bucket,
        subdirectory=bucket_subdirectory
    )
    print(f"Found {len(existing_files)} files on bucket {output_bucket}/{bucket_subdirectory}, e.g. {existing_files[0:3]}")

    #  get the subset of files to upload
    existing_files = [file.split("/")[-1] for file in existing_files]
    new_files = sorted([x for x in downloaded_soho_files if x.split("/")[-1] not in existing_files])

    print(f"Will upload {len(new_files)} files")
    print(new_files[0:10])

    # Want to upload these files to the cloud with the file paths: SOHO/YEAR/FILE
    for local_file in new_files:
        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket,
            source_file_name=local_file,
            new_file_name=f"SOHO/{this_year}/{local_file.split('/')[-1]}",
            metadata={
                "data_source": "SOHO",
                "satellite": "SOHO"
                }
        )
