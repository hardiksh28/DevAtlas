#!/bin/sh
# Daily pg_dump -> gzip -> upload to the same S3/MinIO bucket the app
# already uses (OBJECT_STORAGE_* — see apps/api/app/core/config.py).
# Retention is a bucket lifecycle rule (see docs/architecture/DEPLOYMENT.md),
# not scripted here — S3 already does expiring objects natively.
set -eu

export PGPASSWORD="$POSTGRES_PASSWORD"
export AWS_ACCESS_KEY_ID="$OBJECT_STORAGE_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$OBJECT_STORAGE_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="$OBJECT_STORAGE_REGION"

endpoint_flag=""
if [ -n "${OBJECT_STORAGE_ENDPOINT_URL:-}" ]; then
  endpoint_flag="--endpoint-url $OBJECT_STORAGE_ENDPOINT_URL"
fi

run_backup() {
  timestamp=$(date -u +%Y%m%dT%H%M%SZ)
  file="/tmp/${POSTGRES_DB}-${timestamp}.sql.gz"
  echo "[backup] dumping ${POSTGRES_DB} -> $file"
  pg_dump -h postgres -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$file"
  echo "[backup] uploading to s3://${OBJECT_STORAGE_BUCKET}/backups/"
  aws s3 cp $endpoint_flag "$file" "s3://${OBJECT_STORAGE_BUCKET}/backups/$(basename "$file")"
  rm -f "$file"
}

# ponytail: a daily sleep-loop instead of a cron daemon — one job, one
# schedule, one less package. Swap for real cron if more schedules show up.
while true; do
  run_backup
  sleep 86400
done
