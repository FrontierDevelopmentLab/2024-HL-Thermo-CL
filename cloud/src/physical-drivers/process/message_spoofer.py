class CloudEventSpoof:
    def __init__(self, bucket_name, file_name) -> None:

        # expected keys
        self.data = {
            # Set random value
            "id": "event_id",
            "type": "type",
            "metageneration": "metageneration",
            "timeCreated": "timeCreated",
            "updated": "updated",

            # The only data that matters
            "name": file_name,
            "bucket": bucket_name,
        }

    def __getitem__(self, key):
        return self.data[key]

from main import triggered_on_file_landing_in_bucket

# file_name = "SOHO/2000/00_03_03_v4.00"
file_name = "OMNIWEB/2000/data_2000_01.txt"
bucket_name = "physical-drivers-landing"
cloud_event = CloudEventSpoof(bucket_name=bucket_name, file_name=file_name)
triggered_on_file_landing_in_bucket(cloud_event)
