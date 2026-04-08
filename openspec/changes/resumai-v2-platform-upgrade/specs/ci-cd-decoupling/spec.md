## ADDED Requirements

### Requirement: Source repository CI performs lint, test, build, and image push only
The `ResumAI` source repository GitHub Actions workflow SHALL contain only CI steps: lint → test → Docker build → push image to Artifact Registry. It SHALL NOT apply any infrastructure changes, update Cloud Run services, or inject application configuration.

#### Scenario: Source repo CI completes successfully
- **WHEN** a commit is pushed to `main`
- **THEN** the CI workflow runs `ruff check`, `pytest`, `npm test`, builds the Docker image tagged with the git SHA, pushes it to Artifact Registry, and dispatches a `workflow_dispatch` event to the `resumai-infra` repository with the image digest

#### Scenario: Source repo CI does not hold application secrets
- **WHEN** the source repo GitHub Actions workflow environment is inspected
- **THEN** no `GEMINI_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, or other application secrets are present; only `WORKLOAD_IDENTITY_PROVIDER` and `SERVICE_ACCOUNT` for Artifact Registry push are configured

#### Scenario: Image tag format includes git SHA
- **WHEN** the CI workflow builds and pushes the image
- **THEN** the image is tagged as `REGION-docker.pkg.dev/PROJECT/resumai/api:GIT_SHA` (e.g., `asia-east1-docker.pkg.dev/resumai-prod/resumai/api:a1b2c3d`)

### Requirement: IaC repository CD workflow applies infrastructure and deploys application
The `resumai-infra` repository CD workflow SHALL receive the image digest from the source repo, update the Cloud Run image variable in the Terraform state, and run `terraform apply`.

#### Scenario: CD triggered by image push
- **WHEN** the IaC repo receives a `workflow_dispatch` from the source repo containing `image_digest`
- **THEN** it updates `terraform.tfvars` (or a workspace variable) with the new image digest and runs `terraform apply -auto-approve`

#### Scenario: Deployment is reviewable via Terraform plan
- **WHEN** the IaC repo CD workflow runs `terraform plan`
- **THEN** the plan output is posted as a comment on the triggering PR (for manual deploys) or logged to workflow output (for auto-deploys on `main`)

#### Scenario: CD injects all application configuration
- **WHEN** Terraform configures the Cloud Run service
- **THEN** all environment variables (`GOOGLE_CLOUD_PROJECT`, `CLOUD_SQL_CONNECTION_NAME`, `GCS_BUCKET_NAME`, `LLM_PROVIDER`) are set via the Terraform `env_vars` block; secret references use Secret Manager secret binding (not plain-text values)

### Requirement: No cross-contamination of CI and CD concerns
A source repo workflow SHALL NOT run `terraform apply`, `gcloud run deploy`, or any command that modifies deployed infrastructure. An IaC repo workflow SHALL NOT run application tests or build Docker images.

#### Scenario: PR to source repo cannot trigger a deployment
- **WHEN** a pull request CI run completes on the source repo
- **THEN** no Cloud Run service is updated; only image push to Artifact Registry is permitted on `main` merges, not on PRs

#### Scenario: IaC repo PR shows plan but does not apply
- **WHEN** a pull request is opened in the IaC repo
- **THEN** `terraform plan` runs and posts output; `terraform apply` only runs on merges to `main`
