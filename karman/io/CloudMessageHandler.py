from google.cloud import pubsub_v1
import json

class CloudMessageHandler:
    def __init__(self, project_id: str, topic_name: str):
        self._project_id = project_id
        self._topic_name = topic_name

        self.publisher = pubsub_v1.PublisherClient() 
        self.topic_path = self.publisher.topic_path(project_id, topic_name)

    def send_message(self, message: dict, debug: bool):
        message = json.dumps(message)
        message_bytes = message.encode("utf-8")
        print(f"Sending message: {message}")
        if debug:
            return
        future = self.publisher.publish(self.topic_path, data=message_bytes)
        print(future.result())