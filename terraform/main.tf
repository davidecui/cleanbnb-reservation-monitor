# Enable Required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "firestore.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "${var.job_name}-repo"
  description   = "Docker repository for CleanBnB monitor"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# Firestore Database (Native mode)
# Note: Google Cloud only allows one default Firestore database per project.
# To create it via Terraform in an existing project, it's often better to assume it exists
# or use google_firestore_database. Here we create it if it's a new project.
import {
  to = google_firestore_database.database
  id = "projects/${var.project_id}/databases/(default)"
}

resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.apis]
}

# Service Account for Cloud Run Job
resource "google_service_account" "job_sa" {
  account_id   = "${var.job_name}-sa"
  display_name = "Cloud Run Job SA for ${var.job_name}"
}

# Grant Firestore access to the Job SA
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.job_sa.email}"
}

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler_sa" {
  account_id   = "${var.job_name}-sched-sa"
  display_name = "Cloud Scheduler SA for ${var.job_name}"
}

# Grant Scheduler permission to invoke Cloud Run
resource "google_project_iam_member" "scheduler_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# Secrets
locals {
  secrets = [
    "CLEANBNB_USERNAME",
    "CLEANBNB_PASSWORD",
    "CLEANBNB_PROPERTY_ID",
    "SMTP_PASSWORD",
    "TELEGRAM_BOT_TOKEN"
  ]
}

resource "google_secret_manager_secret" "secrets" {
  for_each = toset(local.secrets)
  secret_id = "${var.job_name}-${replace(each.key, "_", "-")}"

  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

# Grant Secret Access to Cloud Run SA
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = toset(local.secrets)
  secret_id = google_secret_manager_secret.secrets[each.key].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.job_sa.email}"
}

# Workload Identity Pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  
  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# GitHub Actions Deployment Service Account
resource "google_service_account" "github_sa" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions Deployment SA"
}

resource "google_service_account_iam_member" "github_sa_workload_identity" {
  service_account_id = google_service_account.github_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repo}"
}

# Grant deployment permissions to GitHub SA
resource "google_project_iam_member" "github_sa_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.writer",
    "roles/storage.objectAdmin",            # Required for Terraform GCS backend state management
    "roles/iam.serviceAccountUser",         # Required to deploy Cloud Run with job_sa
    "roles/iam.serviceAccountAdmin",        # Required to manage service accounts
    "roles/resourcemanager.projectIamAdmin", # Required to manage project-level IAM roles/members
    "roles/secretmanager.admin",            # Required to manage Secret Manager secrets
    "roles/cloudscheduler.admin",           # Required to manage Cloud Scheduler jobs
    "roles/datastore.owner",                # Required to manage Firestore database
    "roles/serviceusage.serviceUsageAdmin", # Required to enable Google Cloud APIs
    "roles/iam.workloadIdentityPoolAdmin"   # Required to manage Workload Identity Pools/Providers
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_sa.email}"
}

# The Cloud Run Job will be initially deployed via terraform without the actual code image (dummy image)
# Or we can just let GitHub Actions create it. For full IaC, we define it here with a busybox image
# and lifecycle ignore_changes so GitHub Actions can update it.
resource "google_cloud_run_v2_job" "job" {
  name     = var.job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.job_sa.email
      timeout = "600s" # 10 minutes
      
      containers {
        # Using a dummy image initially
        image = "us-docker.pkg.dev/cloudrun/container/job:latest"
        
        env {
          name  = "APP_ENV"
          value = "cloud"
        }
        env {
          name  = "STATE_BACKEND"
          value = "firestore"
        }
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        
        # In a real environment, you might inject other non-secret env vars here.
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
      template[0].template[0].containers[0].env
    ]
  }

  depends_on = [google_project_service.apis]
}

# Cloud Scheduler
resource "google_cloud_scheduler_job" "scheduler" {
  name             = "${var.job_name}-trigger"
  description      = "Triggers the CleanBnB Cloud Run Job daily"
  schedule         = var.schedule
  time_zone        = var.timezone
  region           = var.region
  
  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.job.name}:run"

    oauth_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
  depends_on = [google_project_service.apis]
}
