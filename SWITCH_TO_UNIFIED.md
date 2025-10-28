# How to Switch to Unified Entity

## Quick Start (Do This Now)

### 1. Start Local Claude Service

Open a new terminal and run:

```bash
cd /Users/saady/development/mcp-servers/memory-unified/local-claude-service
bash start.sh
```

This will start the local Claude service and show:
```
============================================================
  Local Claude Service - The Unified Entity
============================================================
Port: 5002
```

**Keep this terminal open!** The service must run continuously.

### 2. Start Ngrok Tunnel

Open another terminal and run:

```bash
ngrok http 5002
```

You'll see:
```
Forwarding   https://XXXXX.ngrok-free.app -> http://localhost:5002
```

**Keep this terminal open too!**

**IMPORTANT**: If the ngrok URL changes, you need to update the secret:

```bash
# Copy the new ngrok URL, then:
echo -n "https://NEW-URL-HERE.ngrok-free.app" | gcloud secrets versions add local-claude-url --data-file=- --project=new-fps-gpt

# Then redeploy Allspark
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
gcloud run deploy allspark-claude --source . --platform managed --region us-central1 --project new-fps-gpt
```

### 3. Verify Everything is Working

```bash
# Test local service
curl http://localhost:5002/health

# Test ngrok tunnel
curl https://XXXXX.ngrok-free.app/health

# Test Allspark
curl https://allspark-claude-958443682078.us-central1.run.app/health
```

All should return `"status":"healthy"`

---

## Now Everything Routes Through Unified Entity!

### Terminal Usage

**No changes needed!** Just use allspark as normal:

```bash
source ~/.zshrc
allspark
```

Your terminal messages will:
1. Go to Allspark cloud
2. Route to your local Claude service (via ngrok)
3. Get processed with full MCP tool access
4. Return to you

### WhatsApp Usage

**No changes needed!** WhatsApp is already configured.

Messages to your WhatsApp Business number will:
1. Hit the WhatsApp webhook
2. Forward to Allspark cloud
3. Route to your local Claude service (via ngrok)
4. Get processed with full capabilities
5. Send response back via WhatsApp

---

## Testing the Unified Entity

### Test from Terminal

```bash
allspark
```

Then type:
```
You: Are you the unified entity? Do you have access to all tools?
```

Claude should confirm it's the unified entity with full tool access.

### Test from WhatsApp

Send a message to your WhatsApp Business number:
```
Are you the unified entity?
```

You should get the same response as terminal - proving it's the SAME entity.

---

## Making It Permanent (Optional)

### Auto-Start on Login

The launchd daemon is already configured. To enable it permanently:

```bash
# Make sure nothing is using port 5002
lsof -ti:5002 | xargs kill -9

# Load the daemon
launchctl load /Users/saady/Library/LaunchAgents/com.allspark.local-claude.plist

# Verify it's running
curl http://localhost:5002/health
```

### Keep Ngrok Running

**Option 1: Ngrok Free (Current)**
- Run `ngrok http 5002` in a terminal
- If it disconnects, restart and update the secret

**Option 2: Ngrok Paid ($8/month)**
- Get a stable URL that never changes
- Configure it to auto-start
- No need to update secrets

To upgrade to ngrok paid:
```bash
# Sign up at https://ngrok.com/pricing
# Get your authtoken
ngrok config add-authtoken YOUR_TOKEN

# Reserve a domain (requires paid plan)
# Then use that domain permanently
```

---

## Troubleshooting

### "Cannot connect to local Claude"

**Check if local service is running:**
```bash
curl http://localhost:5002/health
```

If not running:
```bash
cd /Users/saady/development/mcp-servers/memory-unified/local-claude-service
bash start.sh
```

### "Ngrok tunnel disconnected"

**Restart ngrok:**
```bash
ngrok http 5002
```

**Update the URL in secrets:**
```bash
echo -n "https://NEW-URL.ngrok-free.app" | gcloud secrets versions add local-claude-url --data-file=- --project=new-fps-gpt
```

### "Allspark returns 400 error"

**Check Allspark logs:**
```bash
gcloud run services logs read allspark-claude --region us-central1 --project new-fps-gpt --limit 20
```

**Redeploy if needed:**
```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
gcloud run deploy allspark-claude --source . --platform managed --region us-central1 --project new-fps-gpt
```

---

## Current Status

### What's Working ✅
- Local Claude service (when running)
- Ngrok tunnel (when running)
- Allspark cloud (deployed)
- Secrets configured
- Authentication setup

### What You Need to Do
1. Start local Claude service (terminal 1)
2. Start ngrok (terminal 2)
3. Test with `allspark` command
4. Test with WhatsApp message

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│ You (Terminal or WhatsApp)              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ Allspark Cloud                          │
│ https://allspark-claude-...run.app     │
│ (Stores messages + Routes to local)     │
└────────────────┬────────────────────────┘
                 │
                 │ HTTPS via ngrok
                 ▼
┌─────────────────────────────────────────┐
│ Local Claude Service (Your Mac)        │
│ localhost:5002                          │
│ → Full MCP tool access                  │
│ → Full Anthropic API                    │
│ → Same entity for ALL interfaces        │
└─────────────────────────────────────────┘
```

---

## Next Steps

1. **Now**: Run the Quick Start commands above
2. **Test**: Try both terminal and WhatsApp
3. **Verify**: Confirm both use same entity
4. **Optional**: Setup auto-start daemons

---

**You're ready! Just start the services and you have a unified entity!** 🚀
