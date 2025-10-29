# WhatsApp Webhook Diagnostic Report

**Generated:** 2025-10-28T05:01 UTC

## Issue

Users sending WhatsApp messages receive: **"Sorry, I'm experiencing technical difficulties. Please try again later."**

---

## Your WhatsApp Number

**Display Phone Number:** `+1 414-803-3253` (14148033253)
**Phone Number ID:** `800558376481513`
**Status:** ✅ Active and receiving webhooks from Meta

---

## Root Cause Analysis

### Problem: Allspark 500 Errors

The chain is working UP TO the Allspark, but some requests are failing with 500 errors:

```
04:50:35 POST 500 https://allspark-claude-np7c3nmqfa-uc.a.run.app/chat
04:50:43 [35m[1mPOST /chat HTTP/1.1[0m" 500
04:58:54 POST 500 https://allspark-claude-np7c3nmqfa-uc.a.run.app/chat
04:59:04 [35m[1mPOST /chat HTTP/1.1[0m" 500
```

### Likely Causes

1. **Timeout Issues**
   - Local service is responding slowly (20+ seconds observed)
   - Allspark may be timing out waiting for local response
   - WhatsApp has strict timeout requirements (~10 seconds)

2. **API Key Authentication**
   - Local service requires `LOCAL_CLAUDE_API_KEY` from Secret Manager
   - API Key: `g5-yDCedJ2Et7kn...` (stored in `new-fps-gpt` project)
   - Allspark must send this key when calling local service via ngrok

3. **Anthropic API Processing Time**
   - Local service calls Claude API for every request
   - This adds significant latency to the response chain
   - May be hitting rate limits or slow API responses

---

## Service Status

### ✅ WhatsApp Webhook Service
- **URL:** https://whatsapp-superclaud-958443682078.us-central1.run.app
- **Status:** Healthy
- **Verification:** Working perfectly
- **Allspark URL:** Correctly configured to `https://allspark-claude-np7c3nmqfa-uc.a.run.app`

### ⚠️ Allspark Router
- **URL:** https://allspark-claude-np7c3nmqfa-uc.a.run.app
- **Status:** Healthy (but some 500 errors)
- **Active Conversations:** 3
- **Local Claude:** Connected
- **Issue:** Some POST /chat requests failing with 500

### ✅ Ngrok Tunnel
- **Public URL:** https://ee14c3ef8fe0.ngrok-free.app
- **Local Address:** http://localhost:5002
- **Status:** Active (169 requests processed)
- **Performance:** Stable

### ⚠️ Local Claude Service
- **URL:** http://localhost:5002
- **PID:** 3070 (running)
- **Status:** Responding but SLOW
- **Response Time:** 20+ seconds observed
- **Issue:** Requires API key authentication

---

## Message Flow Analysis

```
✅ WhatsApp User sends message
    ↓
✅ Meta WhatsApp API receives
    ↓
✅ Webhook POST to WhatsApp Service
    ↓
✅ WhatsApp Service forwards to Allspark /chat
    ↓
⚠️  Allspark attempts to call Local Service via ngrok
    ↓ (POTENTIAL FAILURES HERE)
    - Timeout waiting for local response?
    - API key mismatch?
    - Slow Claude API processing?
    ↓
❌ Returns 500 error
    ↓
❌ WhatsApp Service sees error
    ↓
📱 User receives: "Sorry, I'm experiencing technical difficulties"
```

---

## Recommended Fixes

### 1. Check Allspark Configuration

Verify the Allspark has the correct LOCAL_CLAUDE_API_KEY configured:

```bash
gcloud run services describe allspark-claude \
  --region us-central1 \
  --project new-fps-gpt \
  --format="yaml" | grep -A 5 "env:"
```

**Expected:** Should have `LOCAL_CLAUDE_API_KEY` set

**If missing, add it:**
```bash
gcloud run services update allspark-claude \
  --update-secrets=LOCAL_CLAUDE_API_KEY=local-claude-api-key:latest \
  --region us-central1 \
  --project new-fps-gpt
```

### 2. Increase Timeout Settings

Update Allspark to handle slower responses:

```bash
gcloud run services update allspark-claude \
  --timeout=60 \
  --region us-central1 \
  --project new-fps-gpt
```

### 3. Optimize Local Service Response Time

**Option A: Add Caching**
- Cache simple responses locally
- Reduce Claude API calls for repeated queries

**Option B: Async Processing**
- Accept message immediately (return 200)
- Process with Claude asynchronously
- Send response via WhatsApp Send Message API

**Option C: Simpler System Prompt**
- Reduce token count in system prompt
- Faster Claude API responses

### 4. Add Better Error Handling

Update Allspark to:
- Log detailed error information
- Retry failed requests (with backoff)
- Return user-friendly error messages
- Handle timeout gracefully

### 5. Monitor and Debug

**Watch Allspark logs in real-time:**
```bash
gcloud run services logs tail allspark-claude \
  --region us-central1 \
  --project new-fps-gpt
```

**Test direct ngrok connection:**
```bash
# Get API key
LOCAL_KEY=$(gcloud secrets versions access latest \
  --secret=local-claude-api-key \
  --project=new-fps-gpt)

# Test through ngrok
curl -X POST https://ee14c3ef8fe0.ngrok-free.app/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LOCAL_KEY" \
  -d '{"user_id":"test","message":"quick test","interface":"test"}' \
  -w "\nTime: %{time_total}s\n"
```

---

## Quick Test Commands

### Test Local Service Directly
```bash
LOCAL_KEY=$(gcloud secrets versions access latest --secret=local-claude-api-key --project=new-fps-gpt)

curl -X POST http://localhost:5002/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LOCAL_KEY" \
  -d '{"user_id":"test","message":"hi","interface":"test"}' \
  -w "\nResponse Time: %{time_total}s\n"
```

### Test Through Ngrok
```bash
curl -X POST https://ee14c3ef8fe0.ngrok-free.app/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LOCAL_KEY" \
  -d '{"user_id":"test","message":"hi","interface":"test"}' \
  -w "\nResponse Time: %{time_total}s\n"
```

### Test Full Chain (Simulated WhatsApp)
```bash
curl -X POST https://whatsapp-superclaud-958443682078.us-central1.run.app/webhook/meta \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "14148033253",
            "text": {"body": "test"},
            "type": "text"
          }]
        }
      }]
    }]
  }' \
  -w "\nResponse Time: %{time_total}s\n"
```

---

## Summary

**What's Working:**
- ✅ WhatsApp webhook verification
- ✅ Message reception from Meta
- ✅ Allspark routing (sometimes)
- ✅ Ngrok tunnel
- ✅ Local service (when given correct API key)

**What's Broken:**
- ❌ Inconsistent Allspark → Local communication
- ❌ Slow response times (>20 seconds)
- ❌ 500 errors on some requests
- ❌ Users seeing "technical difficulties" message

**Next Steps:**
1. Verify Allspark has correct API key configured
2. Increase timeout settings
3. Monitor logs during live test
4. Optimize local service response time
5. Add better error handling and retry logic

---

## Your WhatsApp Number Again

Send test messages to: **+1 (414) 803-3253**

This number is already configured and receiving webhooks from Meta!
