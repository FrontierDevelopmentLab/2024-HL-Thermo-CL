import pandas as pd
from influxdb_client import InfluxDBClient
import os
import yaml
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.exceptions import InfluxDBError
from influxdb_client.rest import ApiException


# import logging
# import sys
# root = logging.getLogger()
# root.setLevel(logging.DEBUG)
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# root.addHandler(handler)


class InfluxDBManager:
    """
    InfluxDBManager class to interact with InfluxDB.
    """

    def __init__(self):

        credentials = self._load_credentials()

        self._url = credentials['url']
        self._org = credentials['org']
        self._token = credentials['token']
        self._bucket = credentials['bucket']
        TIMEOUT_SECONDS = 60
        TIMEOUT_MS = TIMEOUT_SECONDS * 1000
        self.client = InfluxDBClient(
            url=self._url, org=self._org, token=self._token, timeout=TIMEOUT_MS)
        
        print(f"Initialized influxdb client with bucket: {self._bucket}, org: {self._org}, url: {self._url}.")



    def _load_credentials_local(self) -> dict[str]:
        credentials_file = f"{os.environ['CREDENTIALS']}/influxdb.yaml"
        with open(credentials_file, 'r') as file:
            credentials = yaml.safe_load(file)['influxdb']
        return credentials

    def _load_credentials_cloud(self) -> dict[str]:
        return {
            "org": "FDL",
            "bucket": "hl-therm-influxdb",
            "url": os.environ["INFLUXDB_URL"],
            "token": os.environ["INFLUXDB_TOKEN"]
        }


    def _load_credentials(self) -> dict[str]:
        if "IS_CLOUD" in os.environ: # note this env variable defined in terraform pubsub-cloudfunction main.tf
            return self._load_credentials_cloud()
        else:
            return self._load_credentials_local()

    def write(self, data, measurement, field_columns):
        try:
            with self.client.write_api(write_options=SYNCHRONOUS) as write_api:
                response = write_api.write(
                    bucket=self._bucket,
                    org=self._org,
                    record=data,
                    data_frame_measurement_name=measurement,
                    data_frame_field_columns=field_columns,
                    )
            
        except InfluxDBError as error:
            root.exception(f"Error writing to InfluxDB: {error}")
            root.exception(f"Error message: {error.message}, status: {error.status}, reason: {error.reason}")
            raise RuntimeError("Error writing to InfluxDB")

    def query(self, query) -> str:
        query_api = self.client.query_api()
        result = query_api.query(query=query, org=self._org)
        return result
    
    def query_single_table_daterange(self, start, stop, columns) -> pd.DataFrame:

        # Make sure time field is in the columns, otherwise add it.
        if "_time" not in columns:
            columns = ["_time"] + columns

        query= f'''from (bucket: "{self._bucket}") 
|> range(start: {start}, stop: {stop})
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
|> keep(columns: {columns})
'''.replace("\\n", "").replace("'","\"")
        print(query)
        print(query[192:])

        df = self.client.query_api().query_data_frame(query)

        df = df.drop(columns=["result", "table"])

        return df

    # def get_available_measurements(self):
    #     query = f'import "influxdata/influxdb/schema" schema.measurements(bucket: "{self._bucket}")'
    #     print(f"Querying: {query}")
    #     return self.query(query)

    def health(self) -> str:
        return self.client.health()
    
    def get_bucket_names(self) -> list[str]:
        buckets_api = self.client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        return [bucket.name for bucket in buckets]

    def _delete_everything_in_range(self, start, stop):
        """
        Just because you can, doesn't mean you should.
        start: datetime (str | datetime)
        stop: datetime (str | datetime)
        """
        delete_api = self.client.delete_api()
        delete_api.delete(start=start, stop=stop, predicate='', bucket=self._bucket)

    @staticmethod
    def prepare_dataframe_for_upload(df: pd.DataFrame) -> pd.DataFrame:
        df = df.set_index("all__dates_datetime__")
        return df

    def upload_dataframe(self, df: pd.DataFrame, measurement: str, field_columns=None):

        # Make sure the dataframe is in the right format, if there is a KeyError it probably is already in the right format
        try:
            df = self.prepare_dataframe_for_upload(df)
        except KeyError:
            pass 

        if field_columns is None:
            field_columns = df.columns.tolist()

        # Make sure field columns is sorted
        field_columns = sorted(field_columns)

        self.write(data=df, measurement=measurement, field_columns=field_columns)

    def close(self):
        self.client.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
