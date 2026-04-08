## ADDED Requirements

### Requirement: All GCP infrastructure defined as Terraform in `resumai-infra` repository
The system's GCP infrastructure SHALL be defined entirely as Terraform modules in a dedicated `resumai-infra` repository. No GCP resource SHALL be created or modified outside of Terraform except during the initial state import.

#### Scenario: New Cloud Run revision deployed via Terraform
- **WHEN** a new application image digest is passed to the `compute` Terraform module
- **THEN** `terraform apply` updates the Cloud Run service with zero downtime and the change is recorded in git history

#### Scenario: Infrastructure drift detected and blocked
- **WHEN** a developer runs `gcloud run services update` directly (bypassing Terraform)
- **THEN** the next `terraform plan` in CI detects the drift and marks the plan as requiring review before it can be merged

### Requirement: Terraform remote state stored in a dedicated GCS bucket
Terraform state SHALL be stored in a GCS bucket (`resumai-tf-state`) with versioning enabled. State locking SHALL use GCS object lock.

#### Scenario: Concurrent applies are serialised
- **WHEN** two Terraform apply operations start simultaneously
- **THEN** GCS object lock prevents a race condition and the second apply waits until the first lock is released

#### Scenario: Previous state version is recoverable
- **WHEN** a bad `terraform apply` corrupts the state
- **THEN** a previous state version can be restored from the GCS bucket's version history

### Requirement: Terraform module structure covers all resourcing areas
The `resumai-infra` repository SHALL contain the following top-level Terraform modules:

| Module | Resources |
|---|---|
| `compute/` | Cloud Run services (API, worker), traffic splits, min/max instances |
| `database/` | Cloud SQL instance, databases, users, Auth Proxy service account |
| `storage/` | GCS bucket, lifecycle rules, CORS, IAM bucket bindings |
| `secrets/` | Secret Manager secret declarations (values pushed separately outside Terraform) |
| `iam/` | Service accounts, Workload Identity Federation pools and providers, IAM bindings |
| `tasks/` | Cloud Tasks queue configuration, rate limits |

#### Scenario: New environment provisioned from scratch
- **WHEN** `terraform apply -var-file=staging.tfvars` is run against a blank GCP project
- **THEN** all required resources are created and the application is deployable with no manual steps

### Requirement: Workload Identity Federation for keyless GitHub Actions authentication
Neither the `resumai` source repo nor the `resumai-infra` repo SHALL store long-lived GCP service account JSON keys. GitHub Actions SHALL authenticate to GCP via Workload Identity Federation.

#### Scenario: CI pushes image without service account key
- **WHEN** the source repo CI workflow runs in GitHub Actions
- **THEN** it authenticates to Artifact Registry using `google-github-actions/auth` with Workload Identity Federation; no JSON key file is present in the workflow environment

#### Scenario: IaC CD applies Terraform without service account key
- **WHEN** the IaC repo CD workflow runs `terraform apply`
- **THEN** it authenticates to GCP using Workload Identity Federation bound to the `resumai-infra` GitHub repository
