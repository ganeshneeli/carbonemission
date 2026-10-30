#!/usr/bin/env bash
# ==============================================================================
# 🌱 DevFest 2026 Hackathon: Carbon Coach – Cloud Run Deployment Script
# Deploys Carbon Coach to Google Cloud Run with 1-click live URL.
# ==============================================================================
set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}
SERVICE_NAME="carbon-coach"
REGION="${GCP_REGION:-us-central1}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Google Cloud Project ID not detected."
  echo "Please set your project: export GCP_PROJECT_ID='your-gcp-project-id'"
  exit 1
fi

echo "=========================================================="
echo "🌱 Deploying Carbon Coach to Google Cloud Run"
echo "Project:  $PROJECT_ID"
echo "Service:  $SERVICE_NAME"
echo "Region:   $REGION"
echo "=========================================================="

echo "📦 1/2 Building container image with Google Cloud Build..."
gcloud builds submit --project "$PROJECT_ID" --tag "$IMAGE" .

echo "🚀 2/2 Deploying service to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "GROQ_API_KEY=${GROQ_API_KEY:-}"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --platform managed --region "$REGION" --format 'value(status.url)')

echo "=========================================================="
echo "✅ Carbon Coach is live on Google Cloud Run!"
echo "🌐 URL: $SERVICE_URL"
echo "=========================================================="
