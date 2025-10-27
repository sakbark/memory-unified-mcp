#!/bin/bash
# Deploy Allspark Cloud Claude to Cloud Run

set -e

PROJECT_ID="new-fps-gpt"
SERVICE_NAME="allspark-claude"
REGION="us-central1"

echo "⚡ Deploying Allspark Cloud Claude..."

# Build and deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 10 \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --format 'value(status.url)' 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 Service URL: $SERVICE_URL"
    echo ""
    echo "To update your local configuration:"
    echo "export ALLSPARK_URL=$SERVICE_URL"
    echo ""
    echo "Add this to your ~/.zshrc to make it permanent:"
    echo "echo 'export ALLSPARK_URL=$SERVICE_URL' >> ~/.zshrc"
else
    echo ""
    echo "✅ Deployment initiated!"
    echo "⚠️  Could not retrieve service URL (auth may be needed)"
    echo ""
    echo "To get the URL later, run:"
    echo "gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format 'value(status.url)'"
fi
