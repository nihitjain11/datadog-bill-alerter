terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.32.0"
    }
  }
}

provider "google" {
  # Configuration options
  project = var.project
  region  = "us-west1"
  zone    = "us-west1-c"
}

resource "google_storage_bucket" "bucket" {
  name     = "${var.purpose}-cloud-functions-archive-bucket"
  location = "US"
}

data "archive_file" "function_src" {
  type        = "zip"
  source_dir  = "./code"
  output_path = "./archive.zip"
}

resource "google_storage_bucket_object" "archive" {
  bucket = google_storage_bucket.bucket.name
  source = "./archive.zip"
  name   = "${data.archive_file.function_src.output_sha}.zip"
}

resource "google_cloudfunctions_function" "function" {
  name        = "${var.purpose}-function"
  description = "${var.purpose} Function"
  runtime     = "python39"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.topic.id
    # service    = "pubsub.googleapis.com"
    #failure_policy= {}
  }

  https_trigger_security_level = "SECURE_ALWAYS"
  timeout                      = 60
  entry_point                  = "billing"

  environment_variables = {
    DAYS_DELTA         = var.days_delta
    BUDGET             = var.budget
    DD_API_KEY         = var.dd_api_key
    DD_APPLICATION_KEY = var.dd_application_key
    SLACK_WEBHOOK_URL  = var.slack_webhook_url
    # SENDGRID_API_KEY   = var.sendgrid_api_key
    # FROM_EMAIL         = var.from_email
    # TO_EMAIL           = var.to_email
  }
}

# # IAM entry for a single user to invoke the function
# resource "google_cloudfunctions_function_iam_member" "invoker" {
#   project        = google_cloudfunctions_function.function.project
#   region         = google_cloudfunctions_function.function.region
#   cloud_function = google_cloudfunctions_function.function.name

#   role   = "roles/cloudfunctions.invoker"
#   member = "user:${var.invoker_email}"
# }

resource "google_pubsub_topic" "topic" {
  name = "${var.purpose}-topic"
}

resource "google_cloud_scheduler_job" "job" {
  name        = "${var.purpose}-job"
  description = "${var.purpose} job"
  schedule    = var.cron

  pubsub_target {
    # topic.id is the topic's full resource name.
    topic_name = google_pubsub_topic.topic.id
    data       = base64encode("run")
  }
}