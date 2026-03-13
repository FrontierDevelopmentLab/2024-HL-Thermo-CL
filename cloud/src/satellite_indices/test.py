class CloudEventSpoof:
    def __init__(self) -> None:

        # expected keys
        self.data = {
            # Set random value
            "id": "event_id",
            "type": "type",
            "metageneration": "metageneration",
            "timeCreated": "timeCreated",
            "updated": "updated",
            # The only data that matters
            "message": "hello world"
        }

    def __getitem__(self, key):
        return self.data[key]
    
from main import hello_pubsub

hello_pubsub(CloudEventSpoof())
