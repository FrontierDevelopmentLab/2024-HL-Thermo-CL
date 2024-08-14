import json
import base64



class CloudEventSpoof:
    def __init__(self, landing_bucket_name, project, satellite, year) -> None:

        message_data = {"project": project, "bucket": landing_bucket_name, "satellite": satellite, "year": year}    

        message_data = json.dumps(message_data)
        encoded_data = base64.b64encode(message_data.encode('utf-8')).decode('utf-8')

        # expected keys
        self.data = {
            # Set random value
            "id": "event_id",
            "type": "type",
            "metageneration": "metageneration",
            "timeCreated": "timeCreated",
            "updated": "updated",
            # The only data that matters
            "message": {"data" : encoded_data},
            "bucket": landing_bucket_name,
        }

    def __getitem__(self, key):
        return self.data[key]

from main import hello_pubsub

project = "GOES"
satellite = "goes14"
output_bucket = "test_bucket_hl_therm"
year = 2010

hello_pubsub(CloudEventSpoof(landing_bucket_name=output_bucket, project=project, satellite=satellite, year=year))
