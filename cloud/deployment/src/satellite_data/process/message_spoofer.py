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

file_name = "tudelft/version_02/CHAMP_data/CH_DNS_ACC_2007-07_v02.zip"
bucket_name = "satellite-data-landing"
cloud_event = CloudEventSpoof(bucket_name=bucket_name, file_name=file_name)
triggered_on_file_landing_in_bucket(cloud_event)
