# WhatsApp Configuration for Unified Entity

## Current Status

Your WhatsApp service is deployed but pointing to the **old** Allspark URL.

### Current Config (WRONG)
```python
ALLSPARK_URL = 'https://allspark-claude-533184000292.us-central1.run.app'
```

### Correct URL
```python
ALLSPARK_URL = 'https://allspark-claude-np7c3nmqfa-uc.a.run.app'
```

---

## How To Fix

### Option 1: Update via Environment Variable (Recommended)

Update the Cloud Run service without redeploying code:

```bash
gcloud run services update whatsapp-thin-webhook \
  --update-env-vars ALLSPARK_URL=https://allspark-claude-np7c3nmqfa-uc.a.run.app \
  --region us-central1 \
  --project new-fps-gpt
```

### Option 2: Redeploy WhatsApp Service

```bash
cd /Users/saady/development/whatsapp-superclaud

# Update main.py line 25 to:
# ALLSPARK_URL = os.environ.get('ALLSPARK_URL', 'https://allspark-claude-np7c3nmqfa-uc.a.run.app')

# Then redeploy
gcloud run deploy whatsapp-thin-webhook \
  --source . \
  --platform managed \
  --region us-central1 \
  --project new-fps-gpt \
  --allow-unauthenticated
```

---

## How It Works Now

```
WhatsApp User sends message
  ↓
Meta WhatsApp API
  ↓
WhatsApp Webhook Service
  https://whatsapp-thin-webhook-...run.app/webhook/meta
  ↓ (POST to /chat)
Allspark Cloud Service
  https://allspark-claude-np7c3nmqfa-uc.a.run.app/chat
  ↓ (POST to /process)
Ngrok Tunnel
  https://ee14c3ef8fe0.ngrok-free.app/process
  ↓
Local Claude Service (localhost:5002)
  - Full MCP tools
  - Same entity as terminal
  ↓
Response flows back through chain to WhatsApp
```

---

## Verify WhatsApp Service

### 1. Check Current Config

```bash
gcloud run services describe whatsapp-thin-webhook \
  --region us-central1 \
  --project new-fps-gpt \
  --format="yaml" | grep -A 5 "ALLSPARK_URL"
```

### 2. Check Health

```bash
curl https://[your-whatsapp-service-url]/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "whatsapp-thin-webhook",
  "allspark_url": "https://allspark-claude-np7c3nmqfa-uc.a.run.app"
}
```

### 3. Test End-to-End

Send a WhatsApp message to your business number and it should:
1. Receive message at webhook
2. Forward to Allspark
3. Route to local Claude (unified entity)
4. Process with full tools
5. Send response back to WhatsApp

---

## Quick Fix Command

Run this single command to fix the URL:

```bash
gcloud run services update whatsapp-thin-webhook \
  --update-env-vars ALLSPARK_URL=https://allspark-claude-np7c3nmqfa-uc.a.run.app \
  --region us-central1 \
  --project new-fps-gpt
```

Then test by sending a WhatsApp message!

---

## What You'll Get

Once fixed, your WhatsApp messages will be processed by the SAME unified entity as your terminal:

✅ Full MCP tool access from WhatsApp
✅ Same conversational memory
✅ Shared context with terminal
✅ True unified Claude

---

## Files Involved

- `/Users/saady/development/whatsapp-superclaud/main.py` - WhatsApp webhook
- Line 25: `ALLSPARK_URL` configuration
- Line 159: Where it calls Allspark's `/chat` endpoint

---

## After Fixing

Test it by sending a WhatsApp message like:
```
Are you the unified entity? What tools do you have access to?
```

You should get a response confirming it's the unified entity with full tool access - the SAME Claude as in your terminal!
