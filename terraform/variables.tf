variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region for Cloud Run and Artifact Registry"
  default     = "europe-west4"
}

variable "job_name" {
  type        = string
  description = "Name of the Cloud Run Job"
  default     = "cleanbnb-monitor"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository for Workload Identity (format: org/repo)"
}

variable "schedule" {
  type        = string
  description = "Cron expression for Cloud Scheduler"
  default     = "0 8 * * *" # Daily at 8:00 AM
}

variable "timezone" {
  type        = string
  description = "Timezone for Cloud Scheduler"
  default     = "Europe/Rome"
}
