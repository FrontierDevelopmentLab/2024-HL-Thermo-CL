variable "project_id" {
  default = "hl-therm"
}

variable "region" {
  default = "us-central1"
}

variable "zone" {
  default = "us-central1-a"
}

# Variables stored in untracked terraform.tfvars file. Contain user-specific information
variable "credentials_file" {}
variable "service_account_email" {}
variable "label_created_by" {}
variable "label_owned_by" {}
variable "label_contact_number" {}
variable "INFLUXDB_URL" {}
variable "INFLUXDB_TOKEN" {}
