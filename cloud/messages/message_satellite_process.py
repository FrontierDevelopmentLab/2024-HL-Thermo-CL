"""
Script to mimc the trigger-on-land functionality, kickstarted when a file lands in satellite-data-landing
(it mimics the trigger-on-land action).
"""

from GCloudIO import gcloud_ls
import json
import argparse
from TriggerOnLandMimic import TriggerOnLandMimc
import time


def main():

    actual_landing_bucket = "satellite-data-landing"
    contentType= "application/zip"

    trigger_mimic = TriggerOnLandMimc(
        trigger_bucket=actual_landing_bucket,
        cloud_function_name="tf-process-satellite-data",
        topic_name = "eventarc-us-central1-tf-process-satellite-data-950376-937"
    )

    # Everything that is on the landing bucket, but *not* in the processed bucket has failed at some point
    # and we need to reprocess it.


    # Get a list of files from the bucket

    # prefix = f"tudelft/version_01/Swarm_data"
    # prefix = f"tudelft/version_01/GOCE_data"
    # prefix = f"tudelft/version_02/GRACE-FO_data"
    prefix = f"tudelft/version_02/GRACE_data"
    # prefix = f"tudelft/version_02/CHAMP_data"

    processed_files = gcloud_ls("satellite-data-processed", prefix=prefix)
    processed_files = [x.split('/')[-1].replace("db_", "").replace(".parquet", "") for x in processed_files]
    print(f"Found {len(processed_files)} files in satellite-data-processed for {prefix}")

    file_list = gcloud_ls(actual_landing_bucket, prefix=prefix)
    print(f"Found {len(file_list)} files in {actual_landing_bucket} for {prefix}")

    # get the files in file_list that are not in processed_files
    missing_files = [x for x in file_list if x.split("/")[-1].split(".")[0] not in processed_files]
    if "GOCE" not in prefix:
        print("Removing WND files")
        missing_files = [x for x in missing_files if "_WND_" not in x]
    print(f"Found {len(missing_files)} missing files in {actual_landing_bucket} for {prefix}")

    # import sys
    # sys.exit()
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