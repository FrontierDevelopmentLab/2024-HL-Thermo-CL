import json
import os
import requests
from google.cloud import storage

class UploadFailedError(Exception):
    pass

class StorageClient:
    def __init__(self):
        self.storage_client = storage.Client()

    def url_exists(self, web_directory: str) -> bool:
        response = requests.head(web_directory)
        return response.status_code == 200

    def _get_bucket(self, bucket_name: str):
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
        except storage.NotFound:
            raise ValueError(f"Bucket {bucket_name} does not exist.")
        return bucket


    def check_file_exists_on_bucket(self, bucket_name: str, file_name: str) -> bool:
        """
        Checks if a file exists on a bucket

        Args:
            bucket_name: string, name of the bucket
            file_name: string, name of the file

        Returns:
            bool, True if the file exists, False otherwise
        """
        try:
            bucket_client = self._get_bucket(bucket_name)
            blob_client = bucket_client.get_blob(file_name)
            return blob_client is not None
        except Exception as e:
            return False


    def upload_file_to_bucket(self, destination_bucket_name: str, source_file_name: str, new_file_name: str,
                              metadata: dict = None, verbose: bool = False) -> bool:
        try:
            self._upload_file_to_bucket_implementation(destination_bucket_name, source_file_name, new_file_name, metadata, verbose)
            return True
        except UploadFailedError as e:
            print(e)
            return False


    def _upload_file_to_bucket_implementation(self, destination_bucket_name: str, source_file_name: str, new_file_name: str,
                                              metadata: dict = None, verbose: bool = False):
        """
        Uploads a file (source_file_name) to the bucket, will rename the file with new_file_name. Metadata can be added to the file

        Args:
            destination_bucket_name: string, name of the destination GCP bucket
            source_file_name: string, path of the file on your filesystem
            new_file_name: name that the file will have on the GCP bucket
            metadata: dict, metadata that will be attached to the bucket file object
        """

        #  Check that source_file_name exists and is a file
        if not os.path.isfile(source_file_name):
            raise UploadFailedError(f"ERROR: {source_file_name} does not exist or is not a file (it may be a directory).")

        if verbose:
            print(f"will upload file {source_file_name} to bucket {destination_bucket_name} with name {new_file_name}")

        try:
            bucket_client = self._get_bucket(destination_bucket_name)
            blob_client = bucket_client.blob(new_file_name)

            # Set metadata for the blob
            if metadata is not None:
                blob_client.metadata = metadata

            # Upload the blob
            blob_client.upload_from_filename(source_file_name)
            print(f"File {source_file_name} uploaded to {blob_client.name} in bucket {destination_bucket_name}.")
        except Exception as error:
            raise UploadFailedError(
                f"ERROR: unable to upload file {source_file_name} to bucket {destination_bucket_name}. Trace {error}") from error


    def get_metadata_of_file(self, bucket_name: str, file_name: str) -> dict:
        """
        Gets the metadata of a file in a bucket.

        Args:
            bucket_name: string, name of the bucket
            file_name: string, name of the file

        Returns:
            dict, metadata of the file
        """
        try:
            bucket_client = self._get_bucket(bucket_name)
            blob_client = bucket_client.get_blob(file_name)
            return blob_client.metadata
        except Exception as e:
            print(f"ERROR: unable to get metadata for file {file_name} in bucket {bucket_name}.")
            print(e)
            return None


    def augment_metadata(self, bucket_name: str, file_name: str, metadata: dict) -> None:
        """
        Augments the metadata of a file in a bucket.

        Args:
            bucket_name: string, name of the bucket
            file_name: string, name of the file
            metadata: dict, metadata to be added to the file
        """
        try:
            bucket_client = self._get_bucket(bucket_name)
            blob_client = bucket_client.get_blob(file_name)
            existing_metadata = blob_client.metadata
            existing_metadata.update(metadata)
            blob_client.metadata = existing_metadata
            blob_client.patch()
            print(f"File {file_name} in bucket {bucket_name} updated with metadata {metadata}")
        except Exception as e:
            print(f"ERROR: unable to augment metadata for file {file_name} in bucket {bucket_name}.")
            print(e)


    def download_file_from_bucket(self, source_bucket_name: str, bucket_file_name: str, local_file_name: str, debug=False) -> dict:
        if debug:
            print(f"Downloading file {source_bucket_name}/{bucket_file_name} to {local_file_name}")
        source_bucket = self._get_bucket(source_bucket_name)
        source_blob = source_bucket.get_blob(bucket_file_name)
        blob_metadata = source_blob.metadata
        source_blob.download_to_filename(local_file_name)
        return blob_metadata


    def delete_blob(self, bucket_name: str, blob_name: str):
        """Deletes a blob from the bucket."""
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        generation_match_precondition = None

        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request to delete is aborted if the object's
        # generation number does not match your precondition.
        blob.reload()
        generation_match_precondition = blob.generation

        blob.delete(if_generation_match=generation_match_precondition)
        # print(f"Blob {blob_name} deleted.")


    def read_json_from_bucket(self, bucket_name: str, file_name: str) -> dict:
        # Get the blob (file)
        bucket = self._get_bucket(bucket_name)
        blob = bucket.blob(file_name)

        # Read the blob as a string
        json_string = blob.download_as_text()

        # Parse the JSON string
        json_data = json.loads(json_string)

        return json_data


    def bucket_exists(self, bucket_name) -> bool:
        """
        Check if a Google Cloud Storage bucket exists.

        Args:
            bucket_name (str): The name of the GCS bucket.

        Returns:
            bool: True if the bucket exists, False otherwise.
        """

        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            return True
        except storage.NotFound:
            return False


    def list_files_in_bucket_directory(self, bucket_name: str, subdirectory: str) -> list:


        bucket = self._get_bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=subdirectory)
        
        # Ensure subdirectory path ends with a '/'
        if not subdirectory.endswith('/'):
            subdirectory += '/'
        
        # Filter out directories (GCS treats subdirectories as blobs with a trailing '/')
        files = [blob.name for blob in blobs if not blob.name.endswith('/')]
        
        return files
    

        