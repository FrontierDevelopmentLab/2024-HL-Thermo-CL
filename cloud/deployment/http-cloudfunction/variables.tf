
variable "function_name" {
  description = "Name of the cloud function"
}

variable "zip_file_name" {
  description = "Name of the zipped file to store the cloud function source code"
}

variable "function_bucket_name" {
  description = "Name of the bucket to store the cloud function source code"
}

variable "code_source_dir" {
  description = "Path to the directory containing the cloud function source code (on the local machine)"
}

variable "labels" {
  description = "Common labels to be passed to resources"
  type        = map(string)
}

variable "function_entrypoint_name" {
  description = "Name of the function entrypoint"
}

variable "service_account_email" {
  description = "Email of the service account to use for the cloud function"
}

variable "region" {
  description = "Region to deploy resources to"
}

variable "project_id" {
  description = "Project ID"
}

variable "google_vpc_access_connector_id" {
  description = "Statically defined VPC Access Connector (created outside terraform)"
}

variable "ingress_settings" {
  description = "Setting to control ingress traffic"
}