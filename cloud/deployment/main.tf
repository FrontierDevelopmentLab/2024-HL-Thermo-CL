terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.34.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project_id
  region      = var.region
  zone        = var.zone
}

module "messenger_satellite_data" {

  source = "./http-cloudfunction"

  function_name = "tf-messenger-satellite-data"

  function_entrypoint_name = "hello_http"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-satellite-messenger.zip"
  code_source_dir      = "src/satellite_data/message"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  ingress_settings = "ALLOW_ALL"

}

module "ingest_raw_satellite_data" {

  source = "./pubsub-cloudfunction"

  pubsub_topic_name = "tf-ingest-raw-satellite-data"
  function_name     = "tf-ingest-raw-satellite-data"

  function_entrypoint_name = "hello_pubsub"

  max_instance_count = 10
  available_memory   = "4Gi" # 4Gi is the maximum memory available, it needs a lot for the potential big download

  # Setting to control ingress traffic
  ingress_settings = "ALLOW_ALL"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-satellite-ingestion.zip"
  code_source_dir      = "src/satellite_data/ingestion"

  output_bucket_name = "satellite-data-landing"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id
}

module "process_satellite_data" {

  source            = "./trig-on-land-cloudfunction"
  function_name     = "tf-process-satellite-data"
  pubsub_topic_name = "tf-process-satellite-data"

  trigger_bucket_name = "satellite-data-landing"


  function_entrypoint_name = "triggered_on_file_landing_in_bucket"
  max_instance_count       = 500
  available_memory         = "4Gi" # nrlmsise is very memory intensive 


  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-satellite-process.zip"
  code_source_dir      = "src/satellite_data/process"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

}

module "upload_satellite_data" {

  source            = "./trig-on-land-cloudfunction"
  function_name     = "tf-upload-satellite-data"
  pubsub_topic_name = "tf-upload-satellite-data"

  trigger_bucket_name = "satellite-data-processed"


  function_entrypoint_name = "triggered_on_file_landing_in_bucket"
  max_instance_count       = 10
  available_memory         = "1024M"


  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-satellite-upload.zip"
  code_source_dir      = "src/satellite_data/upload"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

}

module "ingest_and_process_satellite_indices" {

  source = "./pubsub-cloudfunction"

  pubsub_topic_name = "tf-ingest-and-process-satellite-indices"
  function_name     = "tf-ingest-and-process-satellite-indices"

  function_entrypoint_name = "hello_pubsub"

  max_instance_count = 10
  available_memory   = "1024M"

  # Setting to control ingress traffic
  ingress_settings = "ALLOW_ALL"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-indices.zip"
  code_source_dir      = "src/satellite_indices"

  output_bucket_name = "sw-indices"


  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id
}

module "ingest_soho_and_omniweb" {
  source = "./pubsub-cloudfunction"

  pubsub_topic_name = "tf-ingest-raw-physical-drivers"
  function_name     = "tf-ingest-raw-physical-drivers"

  function_entrypoint_name = "hello_pubsub"

  max_instance_count = 10
  available_memory   = "4Gi" # 4Gi is the maximum memory available, it needs a lot for the potential big download

  # Setting to control ingress traffic
  ingress_settings = "ALLOW_ALL"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-soho-and-omniweb-ingestion.zip"
  code_source_dir      = "src/physical-drivers/ingestion"

  output_bucket_name = "physical-drivers-landing"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id
}

module "process_soho_and_omniweb" {

  source            = "./trig-on-land-cloudfunction"
  function_name     = "tf-process-physical-drivers"
  pubsub_topic_name = "tf-process-physical-drivers"

  trigger_bucket_name = "physical-drivers-landing"

  function_entrypoint_name = "triggered_on_file_landing_in_bucket"
  max_instance_count       = 500
  available_memory         = "1024M"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-physical-drivers-process.zip"
  code_source_dir      = "src/physical-drivers/process"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

}

module "ingest_goes" {

  source = "./pubsub-cloudfunction"

  pubsub_topic_name = "tf-ingest-goes"
  function_name     = "tf-ingest-goes"

  function_entrypoint_name = "hello_pubsub"

  max_instance_count = 10
  available_memory   = "8Gi"
  available_cpu      = "2"

  # Setting to control ingress traffic
  ingress_settings = "ALLOW_ALL"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-goes-ingestion.zip"
  code_source_dir      = "src/goes/ingestion"

  output_bucket_name = "satellite-data-landing"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

}

module "process_goes" {

  source = "./pubsub-cloudfunction"

  pubsub_topic_name = "tf-process-goes"
  function_name     = "tf-process-goes"

  function_entrypoint_name = "hello_pubsub"

  max_instance_count = 10
  available_memory   = "4Gi"
  available_cpu      = "1"

  # Setting to control ingress traffic
  ingress_settings = "ALLOW_ALL"

  # Place where source code is stored
  function_bucket_name = google_storage_bucket.function_bucket.name
  zip_file_name        = "function-source-goes-process.zip"
  code_source_dir      = "src/goes/process"

  output_bucket_name = "satellite-data-processed"

  # environment variables
  INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
  INFLUXDB_URL   = var.INFLUXDB_URL

  # Virtual Private Cloud Connector ID
  google_vpc_access_connector_id = "hl-therm-vpc-connector"

  # Generic variables
  service_account_email = var.service_account_email
  labels                = local.common_labels
  region                = var.region
  project_id            = var.project_id

}
