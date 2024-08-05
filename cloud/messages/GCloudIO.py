from google.cloud import storage


class GCloudIO:

    def __init__(self, source_bucket_name, destination_bucket_name, debug=False):
        self.client = storage.Client()

        self._source_bucket_name = source_bucket_name
        self._destination_bucket_name = destination_bucket_name

        self.source_bucket = self.client.bucket(source_bucket_name)
        self.destination_bucket = self.client.bucket(destination_bucket_name)
        self.debug = debug

    def copy_file(self, source_file_name, destination_file_name):

        if self.debug:
            print(f"copying file from source bucket {
                  self._source_bucket_name} to desination bucket {self._destination_bucket_name}")
        # Initialize the Google Cloud Storage client
        # Get the source bucket and blob (file) objects
        source_blob = self.source_bucket.blob(source_file_name)
        # print(source_blob)

        # Get the destination bucket and blob objects
        # destination_blob = destination_bucket.blob(destination_file_name)

        # Copy the file from the source to the destination bucket
        self.source_bucket.copy_blob(
            source_blob, self.destination_bucket, destination_file_name)


def gcloud_ls(bucket_name, prefix):
    """List objects in a GCP bucket with a given prefix."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    # Note: The call returns a response only when the iterator is consumed.
    blob_list = []
    for blob in blobs:
        blob_list.append(blob.name)
    return blob_list
