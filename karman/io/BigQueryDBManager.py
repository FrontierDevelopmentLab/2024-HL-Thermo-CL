import hashlib
from google.cloud import bigquery
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import json

def _generate_hash(file_name: str, timestamp: str) -> str:
    """
    Generates a hash key for a given file name and timestamp.
    """
    string_to_hash = f"{file_name},{timestamp}"
    hash_key = hashlib.md5(string_to_hash.encode())
    return hash_key.hexdigest()

class StatusFlag:
    STARTED = "STARTED"
    RETRIEVED = "RETRIEVED"
    INGESTED = "INGESTED"
    CALIBRATED = "CALIBRATED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    FAILED = "FAILED"
    TEST = "TEST"

class BaseMessage(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError
    
    @abstractmethod
    def get_message(self) -> dict:
        raise NotImplementedError
    

class IngestionMessage(BaseMessage):
    def __init__(self, file_name: str, status_flag: StatusFlag, source) -> None:
        self.timestamp: str = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.hash_key: str = _generate_hash(file_name, self.timestamp)
        self.file_name: str = file_name
        self.status_flag: StatusFlag = status_flag
        self.source = source

    def get_message(self) -> dict:
        return {
            'hash_key': self.hash_key,
            'filename': self.file_name,
            'timestamp' : self.timestamp, # Not in test DB this is 'ldts' 
            'status_flag': self.status_flag,
            'source' : self.source,
        }
    
class CalibrationMessage(BaseMessage):
    def __init__(self, hash_key: str, file_name: str, passed_calibration: bool, source: str, original_message: dict) -> None:
        self.hash_key: str = hash_key
        self.passed_calibration: bool = passed_calibration
        self.file_name: str = file_name
        self.timestamp: str = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.original_message = original_message
        self.source = source

    def get_message(self) -> dict:
        return {
            'hash_key': self.hash_key,
            'filename': self.file_name,
            'timestamp' : self.timestamp,
            'status_flag': self.passed_calibration,
            'source' : self.source,
            'original_message' : json.dumps(self.original_message)
        }

class BigQueryDBManager:
    def __init__(self, dataset_id: str, table_id: str) -> None:
        
        self.client = bigquery.Client()
        self.table_ref = self.client.dataset(dataset_id).table(table_id)
        self.table = bigquery.Table(self.table_ref)
        #print(f"Connected to database {dataset_id}.{table_id}")

    """ 
    def create_landing_entry(self, file_name: str, status_flag: StatusFlag) -> None:
        self._create_landing_entry(IngestionMessage(file_name, status_flag))
    """


    def post_landing_entry(self, message: IngestionMessage) -> None:
        """
        Creates a new entry in the database.
        The intention is that this function is only called when a new file is ingested into the pipeline for the first time.
        """
        #row_message = self._create_new_row_message(file_name, status_flag)
        row_message = message.get_message()
        self.send_message(row_message)

    def post_calibration_entry(self, message: CalibrationMessage) -> None:
        self.send_message(message.get_message())
    
    def _create_new_row_message(self, file_name: str, status_flag: str) -> dict:
        """
        Creates a new row message for the database.
        The intention is that this function is only called when a new file is ingested into the pipeline for the first time.
        """

        now: str = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        row_message = {
            'hash_key': self._generate_hash(file_name, now),
            'filename': file_name,
            'ldts' : now,
            'status_flag': status_flag
        }
        
        return row_message
    

    
    def _update_entry(self, hash_key: str, status_flag: str) -> None:
        """
        Updates an entry in the database.
        NOTE: updating the database relise on the row that is being updated not being in the streaming buffer. 
        This means that the row must have been in the database for at least 90 minutes.
        The query_job.result() will throw a BadRequest exception if the row is in the streaming buffer.
        
        WARNING: our current design is for data tables to be insert-only, so in principle this function doesn't need to be used.
        """
        query = f"""
            UPDATE `{self.table_ref}`
            SET status_flag = '{status_flag}'
            WHERE hash_key = '{hash_key}'
        """
        query_job = self.client.query(query)
        query_job.result()  # Wait for the query to complete

    def send_message(self, new_row_message: dict | list[dict]) -> None:
        """
        Sends a message to the database.
        Args:
            new_row_message (dict | list[dict]): A single message or a list of messages to be sent to the database.
        """
        if isinstance(new_row_message, dict):
            self._send_single_message(new_row_message)
        elif isinstance(new_row_message, list):
            self._send_multi_message(new_row_message)
        else:
            raise TypeError("Input message must be a dict or a list of dicts.")

    def _send_single_message(self, new_row_message: dict) -> None:
        return self._send_multi_message([new_row_message])
    
    def _send_multi_message(self, new_rows: list[dict]) -> None:
        print(f"Sending message to DB: {new_rows}")
        errors = self.client.insert_rows_json(self.table_ref, new_rows)  # Make an API request.
        if errors == []:
            #print("New rows have been added.")
            pass
        else:
            print("Encountered errors while inserting rows: {}".format(errors))
