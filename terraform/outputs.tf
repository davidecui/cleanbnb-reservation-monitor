output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The Workload Identity Provider to use in GitHub Actions"
}

output "service_account_email" {
  value       = google_service_account.github_sa.email
  description = "The Service Account to use for GitHub Actions deployment"
}

output "artifact_registry_repository" {
  value       = google_artifact_registry_repository.repo.name
  description = "The Artifact Registry repository name"
}

output "cloud_run_job_name" {
  value       = google_cloud_run_v2_job.job.name
  description = "The Cloud Run Job name"
}
