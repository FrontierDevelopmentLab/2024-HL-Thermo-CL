"""
This cloud function is used to trigger the ingestion chain for the "satellite_data".
The function is triggered pub/sub, although nothing is required in the pub/sub message, just the fact that a message is sent to the topic.
(This could have been done by a HTTP trigger)

Once the function is triggered, it creates a message for each satellite in SatelliteCollection, and sends a message to the "ingest-raw-satellite-data" topic.
"""

import functions_framework
from karman.io import CloudMessageHandler
from karman.enums import SatelliteCollection
from karman.enums import Satellite


def create_a_message(satellite: Satellite) -> dict:

    message = {
        "project": satellite.name,
        "bucket": "satellite-data-landing",
        "data_path": satellite.data_path
    }

    return message


# @functions_framework.http
# def hello_http(request):
    
@functions_framework.cloud_event
def hello_pubsub(cloud_event):

    print(f"Recieved the following message from pub/sub: {cloud_event.data}")


    project_id = 'hl-therm'
    topic_name = 'tf-ingest-raw-satellite-data'
    messenger = CloudMessageHandler(project_id, topic_name)

    # Send message to download all satellite data. 
    for satellite in SatelliteCollection.get_all_satellites():
        raw_message = create_a_message(satellite)
        messenger.send_message(raw_message, debug=False)    
