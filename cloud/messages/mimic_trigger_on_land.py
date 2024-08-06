"""
Script to mimc the trigger-on-land functionality, kickstarted when a file lands in satellite-data-landing
(it mimics the trigger-on-land action).
"""

from GCloudIO import gcloud_ls
import json
import argparse
from TriggerOnLandMimic import TriggerOnLandMimc


def main():

    actual_landing_bucket = "satellite-data-landing"
    contentType = "application/zip"


    trigger_mimic = TriggerOnLandMimc(
        trigger_bucket="satellite-data-landing",
        cloud_function_name="tf-process-satellite-data",
        topic_name = "eventarc-us-central1-tf-process-satellite-data-351031-719"
    )


    # Get a list of files from the bucket
    prefix = f"tudelft/version_02/GRACE_data"
    prefix = f"tudelft/version_02/CHAMP_data"

    file_list = gcloud_ls(actual_landing_bucket, prefix=prefix)

    print(f"Found {len(file_list)} files in {actual_landing_bucket} for {prefix}")

    all_messages = [trigger_mimic.create_a_message(x, contentType) for x in file_list]
    trigger_mimic.concurrent_post(all_messages)

    # for landing_file in file_list:
        # message = trigger_mimic.create_a_message(landing_file, actual_landing_bucket, contentType)
        # print(message)
        # response = trigger_mimic.mimic_curl(message)
        # print(response)
        
 


if __name__ == "__main__":
    main()