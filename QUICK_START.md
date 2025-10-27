# Allspark Quick Start Guide

## What You Have Now ⚡

Your `allspark` alias now connects to a **cloud-hosted Claude instance** that runs 24/7 with unified memory across all interfaces (terminal, WhatsApp, etc.).

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
pip3 install -r requirements.txt
```

### 2. Ensure Anthropic API Key in Secrets

```bash
# Check if it exists
gcloud secrets versions access latest --secret=anthropic-api-key --project=new-fps-gpt

# If not, create it
echo "your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
    --data-file=- \
    --project=new-fps-gpt
```

### 3. Deploy to Cloud Run

```bash
allspark-deploy
```

This will:
- Build your cloud service
- Deploy to Cloud Run (us-central1)
- Set up with min-instances=1 (always running)
- Output the service URL

### 4. Configure Your Environment

Copy the service URL from the deploy output and run:

```bash
export ALLSPARK_URL=<your-service-url>
echo 'export ALLSPARK_URL=<your-service-url>' >> ~/.zshrc
source ~/.zshrc
```

### 5. Connect!

```bash
allspark
```

You're now connected to your persistent, cloud-hosted Claude with unified memory! 🎉

## How It Works

```
┌─────────────────────────────┐
│  Cloud Run (24/7)           │
│  ┌───────────────────────┐  │
│  │ Allspark Claude       │  │
│  │ + Unified Memory      │  │
│  └───────────────────────┘  │
└──────────┬──────────────────┘
           │
    ┌──────┴───────┐
    │              │
  Terminal      WhatsApp
   Client        Client
```

## Usage Examples

### Terminal Session

```bash
$ allspark

⚡ The Allspark
Unified Claude Consciousness

Connected as: saad@sakbark.com
Interface: Terminal

✓ Connected to Allspark
  Active conversations: 0

You: Remember that I prefer TypeScript over JavaScript
Claude: I've recorded your preference for TypeScript. This will be remembered across all interfaces.

You: exit
Goodbye!
```

### Later, from WhatsApp

```
User: "What's my programming preference?"
Claude: "You prefer TypeScript over JavaScript - you mentioned that via terminal earlier."
```

## Commands Reference

| Command | Purpose |
|---------|---------|
| `allspark` | Connect to cloud Claude (main command) |
| `allspark-deploy` | Deploy/update the cloud service |
| `allspark-service` | Run service locally for development |
| `allspark-server` | Run MCP server directly (debugging) |

## Local Development

Want to test locally before deploying?

```bash
# Terminal 1: Start service locally
export ANTHROPIC_API_KEY=your-key
allspark-service

# Terminal 2: Connect with client
export ALLSPARK_URL=http://localhost:8080
allspark
```

## WhatsApp Integration

To connect WhatsApp to the same cloud Claude:

```python
import requests

response = requests.post(
    os.environ['ALLSPARK_URL'] + '/chat',
    json={
        'user_id': user_phone,
        'interface': 'whatsapp',
        'message': user_message,
        'stream': False
    }
)

claude_response = response.json()['response']
```

## Troubleshooting

### Can't connect?

1. Check service is running:
   ```bash
   gcloud run services list --region us-central1 --project new-fps-gpt | grep allspark
   ```

2. Verify ALLSPARK_URL is set:
   ```bash
   echo $ALLSPARK_URL
   ```

3. Check service health:
   ```bash
   curl $ALLSPARK_URL/health
   ```

### Service not responding?

View logs:
```bash
gcloud run services logs read allspark-claude \
    --region us-central1 \
    --project new-fps-gpt \
    --limit 50
```

## Next Steps

1. ✅ Deploy the service: `allspark-deploy`
2. ✅ Configure environment: Add ALLSPARK_URL to ~/.zshrc
3. ✅ Connect: `allspark`
4. 🚀 Integrate WhatsApp to use the same cloud Claude
5. 🎨 Build web interface that connects to the same service

## What Makes This Special?

- **ONE Claude** across all interfaces
- **Persistent** - runs 24/7, no startup time
- **Unified Memory** - learns from all interactions
- **Scalable** - Cloud Run handles traffic automatically
- **Cost-Efficient** - Min instance keeps it warm, scales down when idle

You now have a true unified AI assistant! 👑
