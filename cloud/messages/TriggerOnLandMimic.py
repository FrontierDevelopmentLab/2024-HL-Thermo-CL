import subprocess
import requests
import datetime
import concurrent.futures



class TriggerOnLandMimc:

    def __init__(self, trigger_bucket, cloud_function_name, topic_name) -> None:
        self.project_id = "hl-therm"
        self.location = "us-central1"
        self.trigger_bucket = trigger_bucket
        self.cloud_function_name = cloud_function_name
        self.topic_name = topic_name


    def mimic_curl(self, json_data):

        command = subprocess.run('gcloud auth print-identity-token', shell=True, capture_output=True, text=True).stdout
        identity_token = command.strip() # remove the newline

        headers = {
            'Authorization': f'bearer {identity_token}',
            'Content-Type': 'application/json',
            'ce-id': '1234567890',
            'ce-specversion': '1.0',
            'ce-type': 'google.cloud.storage.object.v1.finalized',
            'ce-time': '2020-08-08T00:11:44.895529672Z',
            'ce-source': f'//storage.googleapis.com/projects/_/buckets/{self.trigger_bucket}',
        }

        response = requests.post(
            f'https://{self.location}-{self.project_id}.cloudfunctions.net/{self.cloud_function_name}',
            headers=headers,
            json=json_data,
            timeout=550,
        )
        return response
    

    def create_a_message(self, landing_file: str, contentType: str):

        now = datetime.datetime.now(datetime.UTC).isoformat(sep='T', timespec='milliseconds')
        now = now + 'Z'

        message_base = {
            "name": landing_file,
            "bucket": self.trigger_bucket,
            "contentType": contentType,
            "metageneration": "1",
            "timeCreated": now,
            "updated": now,
            }

        return message_base


    def concurrent_post(self, json_data_list: list[dict]):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_request = {executor.submit(self.mimic_curl, data): data for data in json_data_list}
            for future in concurrent.futures.as_completed(future_to_request):
                try:
                    response = future.result()
                    print(response.status_code, response.text)
                except Exception as exc:
                    print(f'Request generated an exception: {exc}')