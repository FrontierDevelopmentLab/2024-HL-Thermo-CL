# Bucket to store cloud function(s)
resource "google_storage_bucket" "function_bucket" {
  name                        = "tf-cloud-function-store" # Every bucket name must be globally unique
  location                    = var.region
  uniform_bucket_level_access = true
  labels                      = local.common_labels


}




# data "google_storage_bucket" "satellite_raw_landing_bucket" {
#   name = "satellite-data-landing"
# }