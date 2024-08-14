import json
import base64



class CloudEventSpoof:
    def __init__(self, landing_bucket_name, data_source: str, year: int, month: int) -> None:

        message_data = {"data_source": data_source, "bucket": landing_bucket_name, "year": year, "month": month}
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

output_bucket = "physical-drivers-landing"
# data_source = "SOHO"
data_source = "OMNIWEB"


# for year in range(2009, 2024+1):
#     for month in range(1, 12+1):
#         if year == 2024 and month > 7:
#             break

#         hello_pubsub(CloudEventSpoof(output_bucket, data_source=data_source, year=year, month=month))

hello_pubsub(CloudEventSpoof(output_bucket, data_source="SOHO", year=None, month=None))
