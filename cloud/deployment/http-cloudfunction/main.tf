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

resource "google_cloudfunctions2_function" "http_function" {
  name        = var.function_name
  location    = var.region
  description = "A simple HTTP-triggered Cloud Function"
  labels      = var.labels
  project     = var.project_id

  build_config {
    entry_point = var.function_entrypoint_name
    runtime     = "python311"

    # Build-time environment variables
    environment_variables = {
      BUILD_CONFIG_TEST = "build_test"
      IS_CLOUD          = "true"
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
    ingress_settings      = var.ingress_settings
    service_account_email = var.service_account_email
    available_memory = "512Mi"
    timeout_seconds  = 60
    
    # Run-time environment variables
    environment_variables = {
      IS_CLOUD = "true"
    }
    vpc_connector = var.google_vpc_access_connector_id
    vpc_connector_egress_settings = "ALL_TRAFFIC"

  }



  # event_trigger {
  #   event_type = "http"
  # }
}