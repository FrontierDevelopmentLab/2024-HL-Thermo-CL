from google.cloud import pubsub_v1
import json
from Satellites import SatelliteCollection

"""
Send messages to the ingest-goes-data topic in the hl-therm project.
This will begin the data download process for the specified GOES satellite, for a specific year.

The message sent must have the following informaiton:
- project: (the only acceptable value is GOES)
- bucket: the name of the bucket where the data will be stored
- satellite: the name of the satellite from which the data will be downloaded (this must be one of goes15, goes16, goes17, goes18)
- year: the year of data to download

"""


project_id = 'hl-therm'
topic_name = 'tf-ingest-goes'
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)



def create_a_message(goes_satellite: str, year: int) -> str:

    message = {
        "project": "GOES",
        "satellite": goes_satellite,
        "bucket": "satellite-data-landing",
        "year": year
    }

    message = json.dumps(message)
    return message


def send_message(message, debug: bool):

    message_bytes = message.encode("utf-8")
    print(f"Sending message: {message}")
    if debug:
        return
    future = publisher.publish(topic_path, data=message_bytes)
    print(future.result())


def main():


    for year in range(2022, 2024+1):
        
        goes_satellite = "goes18"
        message = create_a_message(year=year, goes_satellite=goes_satellite)
        send_message(message, debug=False)


if __name__ == "__main__":
    main()
