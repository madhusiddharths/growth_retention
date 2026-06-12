#!/usr/bin/env bash
# Build (linux/amd64), push to Artifact Registry, and deploy both services to Cloud Run.
set -euo pipefail

PROJECT=gen-lang-client-0874026413
REGION=us-central1
REPO=growth-retention
HOST=$REGION-docker.pkg.dev/$PROJECT/$REPO

echo "==> [1/6] Build API image (linux/amd64)"
docker build --platform linux/amd64 -t "$HOST/api:latest" -f api/Dockerfile .
echo "==> [2/6] Push API image"
docker push "$HOST/api:latest"

echo "==> [3/6] Build frontend image (linux/amd64)"
docker build --platform linux/amd64 -t "$HOST/frontend:latest" -f app/Dockerfile .
echo "==> [4/6] Push frontend image"
docker push "$HOST/frontend:latest"

echo "==> [5/6] Deploy API to Cloud Run"
gcloud run deploy gr-api --project "$PROJECT" --image "$HOST/api:latest" --region "$REGION" \
  --port 8000 --memory 1Gi --allow-unauthenticated --quiet
API_URL=$(gcloud run services describe gr-api --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
echo "API_URL=$API_URL"

echo "==> Deploy frontend to Cloud Run (pointed at the API)"
gcloud run deploy gr-frontend --project "$PROJECT" --image "$HOST/frontend:latest" --region "$REGION" \
  --port 8501 --memory 1Gi --allow-unauthenticated --session-affinity \
  --set-env-vars "API_URL=$API_URL/predict,GOOGLE_CLOUD_PROJECT=$PROJECT" --quiet

echo "==> [6/6] Grant BigQuery access to the frontend runtime service account"
PNUM=$(gcloud projects describe "$PROJECT" --format 'value(projectNumber)')
SA="$PNUM-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role="roles/bigquery.dataViewer" --quiet >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$SA" --role="roles/bigquery.jobUser" --quiet >/dev/null

FE_URL=$(gcloud run services describe gr-frontend --project "$PROJECT" --region "$REGION" --format 'value(status.url)')
echo ""
echo "=================================================================="
echo "  DEPLOYED"
echo "  LIVE DEMO (use this in the portfolio button): $FE_URL"
echo "  API endpoint:                                 $API_URL"
echo "=================================================================="
