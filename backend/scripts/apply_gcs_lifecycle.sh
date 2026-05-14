#!/usr/bin/env bash
# Apply GCS lifecycle policy to auto-delete resume files after 24 hours.
# Run once per bucket (or after bucket recreation):
#   bash scripts/apply_gcs_lifecycle.sh

set -euo pipefail

BUCKET="${GCS_BUCKET_NAME:?GCS_BUCKET_NAME env var is required}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Applying 24h lifecycle policy to gs://${BUCKET} ..."
gsutil lifecycle set "${SCRIPT_DIR}/gcs_lifecycle.json" "gs://${BUCKET}"
echo "Done. Files in gs://${BUCKET} will be auto-deleted after 1 day."
