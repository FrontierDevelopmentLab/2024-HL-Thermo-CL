"""
Script to mimc the trigger-on-land functionality, kickstarted when a file lands in satellite-data-landing
(it mimics the trigger-on-land action).
"""

from GCloudIO import gcloud_ls
from datetime import datetime
import json
from google.cloud import pubsub_v1
import argparse
import subprocess
import requests



def create_a_message(landing_file: str, actual_landing_bucket: str, contentType: str):

    now = datetime.utcnow().isoformat(sep='T', timespec='milliseconds')
    now = now + 'Z'

    message_base = {
        "name": landing_file,
        "bucket": actual_landing_bucket,
        "contentType": contentType,
        "metageneration": "1",
        "timeCreated": now,
        "updated": now,
        }

    return message_base

def mimic_curl(json_data):

    command1 = subprocess.run('gcloud auth print-identity-token', shell=True, capture_output=True, text=True).stdout
    command1 = command1.strip() # remove the newline

    headers = {
        'Authorization': 'bearer ' + command1,
        'Content-Type': 'application/json',
        'ce-id': '1234567890',
        'ce-specversion': '1.0',
        'ce-type': 'google.cloud.storage.object.v1.finalized',
        'ce-time': '2020-08-08T00:11:44.895529672Z',
        'ce-source': '//storage.googleapis.com/projects/_/buckets/us-fdlx-ard-landing-hmi',
    }

    response = requests.post(
        'https://us-central1-us-fdl-x.cloudfunctions.net/us-fdl-x-ard-terraform-trig-on-land-calib-hmi',
        headers=headers,
        json=json_data,
        timeout=550,
    )
    return response

def main(year, month, debug=False):

    actual_landing_bucket = "us-fdlx-ard-landing-hmi-tempoary"
    contentType = "application/zip"


    project_id = 'us-fdl-x'
    topic_name = 'eventarc-us-central1-us-fdl-x-ard-terraform-trig-on-land-calib-hmi-090024-626'
    topic_mame = "us-fdl-x-ard-terraform-trig-on-land-calib-hmi"
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)

    # Get a list of files from the bucket
    file_list = get_one_month_files(year, month, actual_landing_bucket)
    print(f"Found {len(file_list)} files in {actual_landing_bucket} for {year}/{month}")
    for landing_file in file_list:
        message = create_a_message(landing_file, actual_landing_bucket, contentType)
        print(message)

        
        message_bytes = json.dumps(message).encode("utf-8")
        # future = publisher.publish(topic_path, data=message_bytes)
        # print(future.result())


        response = mimic_curl(message)
        print(response)
        break