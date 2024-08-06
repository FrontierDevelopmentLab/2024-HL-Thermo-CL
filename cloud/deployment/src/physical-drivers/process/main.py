import functions_framework
from cloudevents.http import CloudEvent


# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def triggered_on_file_landing_in_bucket(cloud_event: CloudEvent) -> tuple:
    """This function is triggered by a change in a storage bucket.

    Args:
        cloud_event: The CloudEvent that triggered this function.
    Returns:
        The event ID, event type, bucket, name, metageneration, and timeCreated.
    """

    #  hard-code for now
    output_bucket_name = "satellite-data-processed"

    data = cloud_event.data

    print(f"trig on land data recieved: {data}")

    # Extract data from the CloudEvent
    # event_id = cloud_event["id"]
    # event_type = cloud_event["type"]
    landing_bucket_name = data["bucket"]
    # metageneration = data["metageneration"]
    # timeCreated = data["timeCreated"]
    # updated = data["updated"]
    input_file_path = data["name"]  #  File that landed on the bucket

    print(f"File {input_file_path} landed on bucket {landing_bucket_name}")
    landing_file_base_path = input_file_path.rsplit('/', 1)[0]

   