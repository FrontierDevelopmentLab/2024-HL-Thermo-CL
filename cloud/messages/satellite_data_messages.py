from google.cloud import pubsub_v1
import json
from Satellites import SatelliteCollection


project_id = 'hl-therm'
topic_name = 'tf-ingest-raw-satellite-data'
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)



def create_a_message() -> str:

    message = {
        "satellite": SatelliteCollection.CHAMP.name,
        "bucket": "satellite-data-landing",
        "data_path": SatelliteCollection.CHAMP.data_path
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
    message = create_a_message()
    send_message(message, debug=False)


if __name__ == "__main__":
    main()
