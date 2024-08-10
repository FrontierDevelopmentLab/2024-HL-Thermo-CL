from GCloudIO import gcloud_ls
import json
import argparse
from TriggerOnLandMimic import TriggerOnLandMimc
import time

def get_missing_files(prefix, landing_bucket, processed_bucket):
    processed_files = gcloud_ls("physical-drivers-processed", prefix=prefix)
    print(f"Found {len(processed_files)} files in physical-driver-processed for {prefix}")

    raw_data_list = gcloud_ls(landing_bucket, prefix=prefix)
    print(f"Found {len(raw_data_list)} files in {landing_bucket} for {prefix}")

    # snip off .parquet from processed_files
    processed_files = [x.replace(".parquet", "") for x in processed_files]

    missing_files = set(raw_data_list) - set(processed_files)
    print(f"Found {len(missing_files)} missing files in {landing_bucket} for {prefix}")

    return sorted(list(missing_files))

def main():

    landing_bucket = "physical-drivers-landing"
    processed_bucket = "physical-drivers-processed"

    trigger_mimic = TriggerOnLandMimc(
        trigger_bucket=landing_bucket,
        cloud_function_name="tf-process-physical-drivers",
        topic_name = "eventarc-us-central1-tf-process-physical-drivers-176308-963"
    )

    missing_files = []
    for year in range(2000, 2024+1):
        prefix = f"OMNIWEB/{year}"

        if "SOHO" in prefix:
            contentType = "application/octet-stream"
        elif "OMNIWEB" in prefix:
            contentType = "text/plain"
        else:
            raise ValueError("Unknown prefix")

        missing_files.extend(get_missing_files(prefix, landing_bucket, processed_bucket))
    print(f"There are {len(missing_files)} files missing.")

    if len(missing_files) > 25:
        chunk_size = 500 # number of possible VMs 
        for i in range(0, len(missing_files), chunk_size):
            chunk = missing_files[i:i+chunk_size]
            print(f"Processing chunk {i} to {i+chunk_size}")
            all_messages = [trigger_mimic.create_a_message(x, contentType) for x in chunk]
            trigger_mimic.concurrent_post(all_messages)
            print(f"finished concurent cunk {i}")
            time.sleep(300)
    else:
        # missing_files = missing_files[0:1]
        for landing_file in missing_files:
            message = trigger_mimic.create_a_message(landing_file=landing_file, contentType=contentType)
            print(message)
            response = trigger_mimic.mimic_curl(message)
            print(response)


if __name__ == "__main__":
    main()
