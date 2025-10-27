# WhatsApp Webhook Configuration

## Configuration Details

### Webhook URL
```
https://whatsapp-superclaud-958443682078.us-central1.run.app/webhook/meta
```

### Verification Token
```
QsJi2IJNK5vuVNjOIW2R9T0MxvQiY3kHGways9Rz
```

## Step-by-Step Configuration

1. **Go to Meta for Developers**
   - URL: https://developers.facebook.com/apps
   - Login with your Meta account

2. **Select Your WhatsApp Business App**
   - Choose the app you want to configure

3. **Navigate to WhatsApp Configuration**
   - In the left sidebar: **WhatsApp** > **Configuration**

4. **Edit Webhook**
   - Find the "Webhook" section
   - Click **Edit** button

5. **Enter Webhook Details**
   - **Callback URL**: `https://whatsapp-superclaud-958443682078.us-central1.run.app/webhook/meta`
   - **Verify Token**: `QsJi2IJNK5vuVNjOIW2R9T0MxvQiY3kHGways9Rz`
   - Click **Verify and Save**

6. **Subscribe to Events**
   - In the Webhook section, click **Manage**
   - Enable webhook for: **messages**
   - Save changes

## Testing the Webhook

### Test via curl
```bash
curl -X POST "https://whatsapp-superclaud-958443682078.us-central1.run.app/test" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "YOUR_WHATSAPP_NUMBER",
    "message": "Test message from webhook"
  }'
```

### Test via WhatsApp
1. Send a message to your WhatsApp Business number
2. Check logs:
   ```bash
   gcloud run services logs read whatsapp-superclaud \
     --region us-central1 \
     --project new-fps-gpt \
     --limit 20
   ```

## Verification

### Check Webhook Health
```bash
curl https://whatsapp-superclaud-958443682078.us-central1.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "whatsapp-thin-webhook",
  "allspark_url": "https://allspark-claude-958443682078.us-central1.run.app"
}
```

### Check Allspark Connection
The webhook forwards to:
```
https://allspark-claude-958443682078.us-central1.run.app
```

Verify Allspark is healthy:
```bash
curl https://allspark-claude-958443682078.us-central1.run.app/health
```

## Troubleshooting

### Webhook verification fails
- Double-check the verification token matches exactly
- Ensure the callback URL is correct
- Check if service is healthy: `curl [webhook-url]/health`

### Messages not being forwarded
1. Check webhook logs:
   ```bash
   gcloud run services logs read whatsapp-superclaud --limit 20
   ```

2. Verify "messages" event is subscribed in Meta dashboard

3. Test the webhook directly:
   ```bash
   curl -X POST "[webhook-url]/test" \
     -H "Content-Type: application/json" \
     -d '{"phone":"test","message":"test"}'
   ```

### Allspark not responding
1. Check Allspark health:
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/health
   ```

2. Run auto-healing:
   ```bash
   /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service/health_monitor.sh once
   ```

## Security Notes

- ✅ Verification token stored in Google Secret Manager
- ✅ Webhook uses HTTPS only
- ✅ No API keys exposed in logs
- ✅ All secrets injected at runtime

## Configuration Complete

After completing these steps:
- Send a WhatsApp message to your business number
- Claude should respond via the Allspark
- Check that memory is unified (ask Claude what it knows about you)
