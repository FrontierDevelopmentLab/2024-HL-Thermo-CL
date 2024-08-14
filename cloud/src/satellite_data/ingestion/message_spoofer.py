import json
import base64



class CloudEventSpoof:
    def __init__(self, landing_bucket_name, project, data_path) -> None:

        message_data = {"project": project, "bucket": landing_bucket_name, "data_path": data_path}
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

# GRACE A and B
data_path = "/version_02/GRACE_data"
project = "GRACE"

# GRACE C
data_path = "/version_02/GRACE-FO_data"
project = "GRACE"

# SWARM
data_path = "/version_01/Swarm_data"
project = "SWARM"

# GOCE
data_path = "/version_01/GOCE_data"
project = "GOCE"

# CHAMP
data_path = "/version_02/CHAMP_data"
project = "CHAMP" 



hello_pubsub(CloudEventSpoof("satellite-data-landing", project=project, data_path=data_path))
