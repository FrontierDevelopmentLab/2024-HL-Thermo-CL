import base64
import functions_framework
from karman.io import CloudMessageHandler

"""
This cloud function is used to sent messages to the process-goes topic. 
This allows for the processing of GOES data on a per-wavelength basis, as this function sends one message per wavelength.
This function is triggered by a Pub/Sub message, but no data is needed in that message (it is possible that a HTTP trigger could have been used).
It is expected that this function will be triggered by a Cloud Scheculer tigger (or other cron task)
"""

@functions_framework.cloud_event
def hello_pubsub(cloud_event):

    print(f"Recieved the following message from pub/sub: {cloud_event.data}")

    all_wavelengths = [25.6, 28.4, 30.4, 117.5, 121.6, 133.5, 140.5]  # nm

    messinger = CloudMessageHandler(
        project_id="hl-therm",
        topic_name="tf-process-goes",
    )

    for wavelength in all_wavelengths:
        messinger.send_message(
            message={
                "project": "GOES",
                "output_bucket": "satellite-data-processed",
                "wavelength": wavelength,
            },
            debug=False,
        )
