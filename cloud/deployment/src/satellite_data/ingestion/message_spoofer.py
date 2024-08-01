import json
import base64



class CloudEventSpoof:
    def __init__(self, landing_bucket_name, satellite, data_path) -> None:

        message_data = {"satellite": satellite, "bucket": landing_bucket_name, "data_path": data_path}
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

data_path = "/version_02/CHAMP_data"
satellite = "CHAMP"
hello_pubsub(CloudEventSpoof("satellite-data-landing", satellite=satellite, data_path=data_path))
