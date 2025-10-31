#!/bin/bash
# One-command deployment script for Allspark system
# Handles auth automatically via GSM

set -e

PROJECT_ID="new-fps-gpt"
REGION="us-central1"

echo "╔════════════════════════════════════════╗"
echo "║  🚀 Allspark Deployment Script       ║"
echo "║  Deploying Unified Claude System      ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if gcloud is authenticated
echo "🔐 Checking authentication..."
if ! gcloud auth print-access-token > /dev/null 2>&1; then
    echo "⚠️  Not authenticated with gcloud"
    echo "Please run: gcloud auth login"
    echo "Then run this script again"
    exit 1
fi

echo "✅ Authentication OK"
echo ""

# Step 1: Deploy Allspark Cloud Claude
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1/3: Deploying Allspark Cloud Claude"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service

gcloud run deploy allspark-claude \
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

echo ""
echo "✅ Allspark Cloud Claude deployed!"
echo ""

# Get Allspark URL
ALLSPARK_URL=$(gcloud run services describe allspark-claude \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)')

echo "🌐 Allspark URL: $ALLSPARK_URL"
echo ""

# Test Allspark
echo "🧪 Testing Allspark health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $ALLSPARK_URL/health)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ Allspark is healthy!"
else
    echo "⚠️  Allspark health check returned: $HEALTH_STATUS"
fi

echo ""

# Step 2: Deploy WhatsApp Thin Webhook
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2/3: Deploying WhatsApp Thin Webhook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd /Users/saady/whatsapp-claude-webhook

# Backup current main.py if it exists
if [ -f "main.py" ]; then
    BACKUP_NAME="main.py.backup_$(date +%Y%m%d_%H%M%S)"
    cp main.py "$BACKUP_NAME"
    echo "📦 Backed up main.py to $BACKUP_NAME"
fi

# Copy thin webhook as main
cp main_thin_webhook.py main.py

gcloud run deploy whatsapp-claude-webhook \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars PROJECT_ID=$PROJECT_ID,ALLSPARK_URL=$ALLSPARK_URL

echo ""
echo "✅ WhatsApp webhook deployed!"
echo ""

# Get webhook URL
WEBHOOK_URL=$(gcloud run services describe whatsapp-claude-webhook \
    --region $REGION \
    --project $PROJECT_ID \
    --format='value(status.url)')

echo "🌐 Webhook URL: $WEBHOOK_URL"
echo ""

# Test webhook
echo "🧪 Testing webhook health..."
WEBHOOK_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" $WEBHOOK_URL/health)

if [ "$WEBHOOK_HEALTH" = "200" ]; then
    echo "✅ Webhook is healthy!"
else
    echo "⚠️  Webhook health check returned: $WEBHOOK_HEALTH"
fi

echo ""

# Step 3: Configure local environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3/3: Configuring Local Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Update .zshrc with ALLSPARK_URL if not already there
if grep -q "ALLSPARK_URL" ~/.zshrc; then
    echo "ℹ️  ALLSPARK_URL already in .zshrc, updating..."
    # Remove old line
    sed -i.bak "/export ALLSPARK_URL=/d" ~/.zshrc
fi

echo "export ALLSPARK_URL=$ALLSPARK_URL" >> ~/.zshrc
echo "✅ Added ALLSPARK_URL to ~/.zshrc"
echo ""

# Export for current session
export ALLSPARK_URL=$ALLSPARK_URL

echo "╔════════════════════════════════════════╗"
echo "║  ✨ Deployment Complete! ✨           ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📋 Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 Allspark Claude:   $ALLSPARK_URL"
echo "📱 WhatsApp Webhook:  $WEBHOOK_URL"
echo ""
echo "🎯 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Test Terminal Client:"
echo "    source ~/.zshrc"
echo "    allspark"
echo ""
echo "2️⃣  Configure Meta WhatsApp:"
echo "    URL: $WEBHOOK_URL/webhook/meta"
echo "    Token: \$(gcloud secrets versions access latest --secret=whatsapp-webhook-verify-token --project=$PROJECT_ID)"
echo ""
echo "3️⃣  Test WhatsApp:"
echo "    Send a message to your WhatsApp Business number"
echo ""
echo "4️⃣  Monitor logs:"
echo "    gcloud run services logs read allspark-claude --region $REGION --limit 50"
echo "    gcloud run services logs read whatsapp-claude-webhook --region $REGION --limit 50"
echo ""
echo "🎉 You now have a unified Claude across all interfaces!"
