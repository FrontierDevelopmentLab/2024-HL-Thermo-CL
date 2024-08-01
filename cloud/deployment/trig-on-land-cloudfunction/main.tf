data "archive_file" "function_archive_file" {
  type        = "zip"
  output_path = "/tmp/${var.zip_file_name}"
  source_dir  = var.code_source_dir
}

# Object inside bucket, corresponding to zipped file for cloud function
resource "google_storage_bucket_object" "function_zip_object" {
  name   = var.zip_file_name #"function-source-ingestion.zip"
  bucket = var.function_bucket_name
  source = data.archive_file.function_archive_file.output_path # Path to the zipped function source code
}

# Cloud function that will trigger on file landing in bucket (triggered by a `Finalize` event on the bucket)
resource "google_cloudfunctions2_function" "trigger_on_land_function" {

  name        = var.function_name
  location    = var.region
  description = "A function that will trigger when something lands on a bucket"
  labels      = var.labels
  project     = var.project_id

  build_config {
    runtime     = "python311"
    entry_point = var.function_entrypoint_name

    # Build-time environment variables
    environment_variables = {
      BUILD_CONFIG_TEST = "build_test"
      IS_CLOUD = "true"
    }

    # Location of the function source code 
    source {
      storage_source {
        bucket = var.function_bucket_name
        object = google_storage_bucket_object.function_zip_object.name
      }
    }
  }

  service_config {
    max_instance_count = var.max_instance_count
    min_instance_count = var.min_instance_count
    available_memory   = var.available_memory 
    available_cpu      = var.available_cpu
    timeout_seconds    = 540
    # Run-time environment variables
    environment_variables = {
      SERVICE_CONFIG_TEST = "config_test"
      IS_CLOUD = "true"
      INFLUXDB_TOKEN = var.INFLUXDB_TOKEN
      INFLUXDB_URL   = var.INFLUXDB_URL
      GCP_PROJECT_ID      = var.project_id
    }
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
    service_account_email = var.service_account_email
  }

  # 
  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.storage.object.v1.finalized"
    service_account_email = var.service_account_email
    event_filters {
      attribute = "bucket"
      value     = var.trigger_bucket_name
    }
  }

}