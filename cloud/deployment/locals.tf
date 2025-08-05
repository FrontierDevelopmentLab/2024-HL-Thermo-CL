/*****************************************************************************************
Since variables (in variables.tf) cannot be used to create other variables, 
we use locals (in locals.tf) to create variables that can be used in other files.
*****************************************************************************************/

locals {
  common_labels = {
    created_by   = var.label_created_by
    owned_by     = var.label_owned_by
    contact      = var.label_contact_number
    sensitive    = "false"
    project_name = var.project_id
  }
}