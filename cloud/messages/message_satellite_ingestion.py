"""
Send messages to the ingest-raw-satellite-data topic in the hl-therm project.
This will begin the data download process for the specified satellite, taken from the tudelft ftp server.

Files on the ftp server are only updated once per month.
"""

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


def main():

    # Send a message to download the raw data for each satellite
    project_id = 'hl-therm'
    topic_name = 'tf-ingest-raw-satellite-data'
    messenger = CloudMessageHandler(project_id, topic_name)

    for satellite in SatelliteCollection.get_all_satellites():
        raw_message = create_a_message(satellite)
        messenger.send_message(raw_message, debug=False)    


if __name__ == "__main__":
    main()
