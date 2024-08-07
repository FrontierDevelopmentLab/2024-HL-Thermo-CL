import base64
import functions_framework
import json
import os
from karman.io import StorageClient
from glob import glob
from datetime import datetime

from download_soho import SohoDownloader, get_all_years
from download_omniweb import download_omniweb_data_one_month


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

        # For omniweb, the message can have the optional "year" and "month" fields
        year = message.get("year", None)
        month = message.get("month", None)
        ingest_omniweb(output_bucket, year, month)
    else:
        raise ValueError(f"Unknown data source: {data_source}")

def get_previous_month():
    return datetime.now().month - 1

def ingest_omniweb(output_bucket: str, year: int | None, month: int|None):

    if year is None:
        year = get_all_years()[-1]

    if month is None:
        month = get_previous_month()

    output_dir = "/shared/raw/omniweb"
    downloaded_file = download_omniweb_data_one_month(year=year, month=month, omiweb_data_dir=output_dir)
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
            new_file_name=f"OMNIWEB/{year}/{local_file.split('/')[-1]}",
            metadata={
                "data_source": "OMNIWEB",
                "satellite": "OMNIWEB",
                "year": year,
                "month": month
                }
        )

    # delete the locally downloaded files
    for local_file in downloaded_files:
        os.remove(local_file)


    

def ingest_soho(output_bucket):

    """
    Will download the latest month's SOHO data to the local machine, and then upload those files to the cloud.
    """

    # Get the years to download, we probably only ever want the most recent data
    this_year = get_all_years()[-1]

    # get the current month in "MM" format
    this_month_MM_str = datetime.now().strftime("%m")

    # get this year into "YY" format
    this_year_YY_str = f"{this_year:02}"


    output_dir = "/shared/raw/soho"

    downloader = SohoDownloader(output_dir)
    downloader.download_data_parallel([this_year])

    #  find all the files that have been downloaded
    downloaded_files = glob(f"{output_dir}/{this_year}/{this_year_YY_str}_{this_month_MM_str}_*")

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
                "satellite": "SOHO",
                "year": this_year,
                }
        )

    # remove the locally downloaded files
    for local_file in downloaded_soho_files:
        os.remove(local_file)
