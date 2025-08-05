import functions_framework
import os
from karman.io import StorageClient

# from karman.scripts.download_sw_indices import download_all_indices
# from karman.scripts.process_sw_proxy_data import process_sw_proxy_data
from download_sw_indices import download_all_indices
from process_sw_proxy_data import process_sw_proxy_data
from merge_sw_and_satellites import join_sw_indices_files


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def hello_pubsub(cloud_event):

    print(f"Hello from the cloud: {cloud_event.data}")

    # satellite = cloud_event.data["message"]["satellite"]
    # output_bucket = cloud_event.data["message"]["bucket"]
    output_bucket = "sw-indices"


    # Create a directory on the local filesystem to store the data
    raw_data_dir = "/tmp/raw_data"
    processed_data_dir = "/tmp/processed_data"
    os.mkdir(raw_data_dir)
    os.mkdir(processed_data_dir)

    # Download the indices 
    print("Downloading satellite indices ...")
    downloaded_files = download_all_indices(raw_data_dir)

    # upload this data to the bucket
    storage_client = StorageClient()
    for file in downloaded_files:

        destination_file_name = f"raw/{file.split('/')[-1]}"

        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket, 
            source_file_name=file, 
            new_file_name=destination_file_name
            )

    # Process the downloaded files locally
    set_output, celestrack_output = process_sw_proxy_data(
        input_dir=raw_data_dir, 
        output_dir=processed_data_dir
        )
    
    # Upload the processed data to the bucket
    for file in [set_output, celestrack_output]:

        destination_file_name = f"processed/{file.split('/')[-1]}"

        storage_client.upload_file_to_bucket(
            destination_bucket_name=output_bucket, 
            source_file_name=file, 
            new_file_name=destination_file_name
        )

    # combine the two CSV files and upload to the bucket
    combined_df = join_sw_indices_files(set_output, celestrack_output)
    combined_df.to_parquet(f"{processed_data_dir}/combined_indices.parquet", index=False)

    storage_client.upload_file_to_bucket(
        destination_bucket_name=output_bucket, 
        source_file_name=f"{processed_data_dir}/combined_indices.parquet", 
        new_file_name="processed/combined_indices.parquet"
        )
