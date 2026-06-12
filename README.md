# CleanBnB Reservation Monitor

A Python application that logs into the CleanBnB owners portal, fetches new reservations, and sends notifications (Email / Telegram) when a new reservation is found. It persists state so the same reservation is not notified twice.

## Architecture

The project supports two execution modes:

### 1. Local Mode (Development)
- Runs via plain Python or Docker.
- Secrets and config loaded from a `.env` file.
- State is persisted to a local file (`data/reservations_state.json`).
- Does not require GCP credentials.

### 2. Cloud Mode (Production)
- Executed as a Cloud Run Job on Google Cloud.
- Triggered daily by Cloud Scheduler.
- Configuration is provided as environment variables; secrets are injected from GCP Secret Manager.
- State is stored in Google Cloud Firestore.
- Deployed via GitHub Actions using Workload Identity Federation.

## Local Development Setup

1. **Clone and Setup Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and fill out `CLEANBNB_USERNAME`, `CLEANBNB_PASSWORD`, `CLEANBNB_PROPERTY_ID`, etc.*

3. **Run Locally:**
   ```bash
   make run-local
   # Or using Python directly:
   # python -m app.main
   ```

4. **Run Tests:**
   ```bash
   make test
   ```

## Cloud Deployment Architecture

The application is deployed using Terraform and GitHub Actions.

- **Firestore**: Used as a key-value store to keep track of notified `reservation_id`s.
- **Secret Manager**: Stores the CleanBnB credentials, SMTP passwords, and Telegram tokens securely.
- **Cloud Run Job**: The application is packaged as a container and runs as a Serverless Job.
- **Cloud Scheduler**: A cron job triggers the Cloud Run Job every 24 hours.

### Terraform Bootstrapping

Before deploying via GitHub Actions, you need to bootstrap Terraform:

1. Authenticate locally with `gcloud auth application-default login`.
2. Ensure you have the required GCP permissions.
3. Create a GCS bucket for Terraform remote state (e.g. `your-project-tfstate`).
4. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and set your values.
5. Run:
   ```bash
   cd terraform
   terraform init -backend-config="bucket=your-project-tfstate"
   terraform apply
   ```

This will create all resources including Workload Identity Federation for GitHub Actions.

### GitHub Actions CI/CD

The pipeline (`.github/workflows/deploy.yml`) is triggered on merges to `main`. It will:
1. Authenticate to GCP using Workload Identity Federation.
2. Build the Docker image.
3. Push to Google Artifact Registry.
4. Run `terraform apply` to update the Cloud Run Job with the new image.

### Reservation Deduplication

Reservations are uniquely identified by a SHA-256 fingerprint generated from stable fields:
`guest_name`, `portal`, `checkin`, `checkout`, `apartment`, and `status`.

When the app runs, it compares the current fetched reservations against the persisted state (Local File or Firestore). Only reservations with novel fingerprints will trigger notifications.

## Troubleshooting

- **Login Failures**: If CleanBnB updates their portal login flow, the parser in `app/clients/cleanbnb.py` might need updating. It currently parses dynamic hidden fields automatically.
- **Parsing Errors**: If the reservation table structure changes, check `app/parsers/reservations.py` and run the unit tests with an updated HTML mock.
- **State Backend**: If the app fails to save state, verify that `APP_ENV=local` uses `STATE_BACKEND=file`, and `APP_ENV=cloud` uses `STATE_BACKEND=firestore`.
