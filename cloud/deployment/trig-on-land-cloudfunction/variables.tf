variable "labels" {
  description = "Common labels to be passed to resources"
  type        = map(string)
}

variable "function_name" {
  description = "Name of the cloud function"
}

variable "max_instance_count" {
  description = "Maximum number of instances of the cloud function"
}

variable "min_instance_count" {
  description = "Minimum number of instances of the cloud function"
  default     = 0
}

variable "region" {
  description = "Region to deploy resources to"
}

variable "project_id" {
  description = "Project ID"
}

variable "function_bucket_name" {
  description = "Name of the bucket to store the cloud function source code"
}

variable "zip_file_name" {
  description = "Name of the zipped file to store the cloud function source code"
}

variable "code_source_dir" {
  description = "Path to the directory containing the cloud function source code (on the local machine)"
}


variable "service_account_email" {
  description = "Email of the service account to use for the cloud function"
}

variable "available_cpu" {
  description = "Number of CPUs available to the cloud function"
  type        = string
  default     = "1"
}

variable "available_memory" {
  description = "Amount of memory available to the cloud function"
  type        = string
  default     = "2Gi"
}

variable "function_entrypoint_name" {
  description = "Name of the function entrypoint"
}

variable "trigger_bucket_name" {
  description = "Name of the bucket to trigger the cloud function"
}

variable "INFLUXDB_TOKEN" {
  description = "access token for influxdb"
}

variable "INFLUXDB_URL" {
  description = "url for influxdb"
}

variable "google_vpc_access_connector_id" {
  description = "Statically defined VPC Access Connector (created outside terraform)"
}