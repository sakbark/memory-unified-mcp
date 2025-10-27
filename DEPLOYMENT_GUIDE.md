# Allspark Deployment Guide

## New Architecture: One Cloud Claude, Multiple Interfaces

This guide walks you through deploying the **unified cloud-hosted Claude service** that serves all interfaces (terminal, WhatsApp, web, etc.).

## Architecture Overview

```
                    ┌─────────────────────────────┐
                    │  Firestore (Unified Memory) │
                    │  - Conversations            │
                    │  - Entities & Facts         │
                    │  - Context Windows          │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Allspark Cloud Claude      │
                    │  (Cloud Run - Always On)    │
                    │  - Claude API Integration   │
                    │  - Memory Management        │
                    │  - REST API                 │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
       ┌──────▼──────┐      ┌─────▼──────┐     ┌─────▼──────┐
       │  Terminal   │      │  WhatsApp  │     │    Web     │
       │   Client    │      │   Webhook  │     │  Interface │
       │ (Rich CLI)  │      │  (Thin)    │     │  (Future)  │
       └─────────────┘      └────────────┘     └────────────┘
```

## Prerequisites

1. **Google Cloud Project**: `new-fps-gpt`
2. **Secrets in Google Secret Manager**:
   - `anthropic-api-key` (for Claude API)
   - `whatsapp-webhook-verify-token` (for Meta webhook)
   - `meta-whatsapp-api-token` (for WhatsApp API)
   - `whatsapp-business-account-config` (Meta account config)
3. **gcloud CLI** configured and authenticated

## Step 1: Deploy Allspark Cloud Claude Service

This is the core service that handles all Claude interactions.

### 1.1 Navigate to the service directory

```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
```

### 1.2 Verify secrets exist

```bash
# Check Anthropic API key
gcloud secrets versions access latest --secret=anthropic-api-key --project=new-fps-gpt

# If missing, create it
echo "your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
    --data-file=- \
    --project=new-fps-gpt
```

### 1.3 Deploy to Cloud Run

```bash
./deploy.sh
```

Or manually:

```bash
gcloud run deploy allspark-claude \
    --source . \
    --platform managed \
    --region us-central1 \
    --project new-fps-gpt \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 10 \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --set-env-vars GOOGLE_CLOUD_PROJECT=new-fps-gpt
```

### 1.4 Get and save the service URL

```bash
ALLSPARK_URL=$(gcloud run services describe allspark-claude \
    --region us-central1 \
    --project new-fps-gpt \
    --format='value(status.url)')

echo $ALLSPARK_URL
```

### 1.5 Configure your environment

```bash
# Add to your shell config
export ALLSPARK_URL=<your-service-url>
echo "export ALLSPARK_URL=$ALLSPARK_URL" >> ~/.zshrc
source ~/.zshrc
```

### 1.6 Test the service

```bash
# Health check
curl $ALLSPARK_URL/health

# Test chat (non-streaming)
curl -X POST $ALLSPARK_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "interface": "terminal",
    "message": "Hello!",
    "stream": false
  }'
```

## Step 2: Deploy WhatsApp Thin Webhook

This lightweight webhook forwards WhatsApp messages to the cloud Claude service.

### 2.1 Navigate to WhatsApp service directory

```bash
cd /Users/saady/development/whatsapp-superclaud
```

### 2.2 Deploy the thin webhook

```bash
./deploy_thin.sh
```

This will:
- Verify Allspark Cloud Claude is deployed
- Backup your current main.py
- Deploy the thin webhook version
- Configure it to use the Allspark URL

### 2.3 Get the webhook URL

```bash
WEBHOOK_URL=$(gcloud run services describe whatsapp-superclaud \
    --region us-central1 \
    --project new-fps-gpt \
    --format='value(status.url)')

echo "WhatsApp Webhook: $WEBHOOK_URL/webhook/meta"
```

### 2.4 Configure Meta WhatsApp

1. Go to https://developers.facebook.com/apps
2. Select your WhatsApp Business App
3. Go to **WhatsApp > Configuration**
4. Set **Callback URL**: `<WEBHOOK_URL>/webhook/meta`
5. Get verify token:
   ```bash
   gcloud secrets versions access latest \
       --secret=whatsapp-webhook-verify-token \
       --project=new-fps-gpt
   ```
6. Enter the verify token and click **Verify and Save**
7. Subscribe to **messages** events

### 2.5 Test WhatsApp integration

```bash
# Test endpoint
curl -X POST "$WEBHOOK_URL/test" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "your-phone-number",
    "message": "Hello from test!"
  }'
```

Or just send a WhatsApp message to your business number!

## Step 3: Use Terminal Client

### 3.1 Install terminal client dependencies

```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
pip3 install -r requirements.txt
```

### 3.2 Connect to Allspark

```bash
allspark
```

This will:
- Check if ALLSPARK_URL is set
- Connect to your cloud Claude instance
- Provide a rich terminal interface

## Step 4: Verify End-to-End

### Test 1: Terminal → Allspark

```bash
$ allspark

You: Remember that I prefer TypeScript
Claude: I've recorded your preference for TypeScript...

You: exit
```

### Test 2: WhatsApp → Allspark

Send a message via WhatsApp:
```
You: What's my programming preference?
Claude: You prefer TypeScript - you mentioned that via terminal earlier.
```

### Test 3: Check Memory

```bash
# View Firestore data
gcloud firestore export gs://new-fps-gpt-backup/firestore-export
```

Or check via Cloud Console:
https://console.cloud.google.com/firestore/data

## Monitoring & Debugging

### View Allspark Logs

```bash
gcloud run services logs read allspark-claude \
    --region us-central1 \
    --project new-fps-gpt \
    --limit 50
```

### View WhatsApp Webhook Logs

```bash
gcloud run services logs read whatsapp-superclaud \
    --region us-central1 \
    --project new-fps-gpt \
    --limit 50
```

### Check Service Status

```bash
# Allspark
gcloud run services describe allspark-claude \
    --region us-central1 \
    --project new-fps-gpt

# WhatsApp
gcloud run services describe whatsapp-superclaud \
    --region us-central1 \
    --project new-fps-gpt
```

### View Active Conversations

```bash
curl $ALLSPARK_URL/conversations
```

## Troubleshooting

### "Cannot connect to Allspark"

1. Check service is deployed:
   ```bash
   gcloud run services list --region us-central1 --project new-fps-gpt
   ```

2. Verify ALLSPARK_URL is set:
   ```bash
   echo $ALLSPARK_URL
   ```

3. Test health endpoint:
   ```bash
   curl $ALLSPARK_URL/health
   ```

### WhatsApp messages not working

1. Check webhook logs:
   ```bash
   gcloud run services logs read whatsapp-superclaud --limit 20
   ```

2. Verify webhook configuration in Meta dashboard

3. Test with curl:
   ```bash
   curl -X POST "$WEBHOOK_URL/test" \
     -H "Content-Type: application/json" \
     -d '{"phone": "your-number", "message": "test"}'
   ```

### Allspark returning errors

1. Check if Anthropic API key is valid:
   ```bash
   gcloud secrets versions access latest --secret=anthropic-api-key
   ```

2. View detailed logs with errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=allspark-claude AND severity>=ERROR" \
       --limit 10 \
       --format json
   ```

## Updating Services

### Update Allspark

```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
# Make your changes to server.py
./deploy.sh
```

### Update WhatsApp Webhook

```bash
cd /Users/saady/development/whatsapp-superclaud
# Make your changes to main_thin_webhook.py
./deploy_thin.sh
```

## Cost Optimization

### Current Configuration

- **Allspark**: min-instances=1 (always warm, ~$30/month idle)
- **WhatsApp**: min-instances=0 (scales to zero, pay per use)

### To Reduce Costs

If you want to save money and can tolerate cold starts:

```bash
# Update Allspark to scale to zero
gcloud run services update allspark-claude \
    --min-instances 0 \
    --region us-central1 \
    --project new-fps-gpt
```

Note: This adds ~10-30 second cold start delay when first accessed.

## Architecture Benefits

✅ **Single Source of Truth**: One Claude instance across all interfaces
✅ **Unified Memory**: All conversations and knowledge synchronized
✅ **Easy Maintenance**: Update one service, affects all interfaces
✅ **Scalable**: Cloud Run auto-scales based on demand
✅ **Cost-Efficient**: Thin webhooks have minimal overhead
✅ **Extensible**: Easy to add new interfaces (web, mobile, etc.)

## Next Steps

1. ✅ Deploy Allspark Cloud Claude
2. ✅ Deploy WhatsApp thin webhook
3. ✅ Test terminal client
4. 🚀 Add web interface
5. 🚀 Add Slack integration
6. 🚀 Add mobile app

---

**You now have a truly unified AI assistant! 👑**
