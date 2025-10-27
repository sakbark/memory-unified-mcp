# Allspark Cloud Claude Service

A persistent, cloud-hosted Claude instance with unified memory across all interfaces.

## Architecture

```
┌─────────────────────────────────────────┐
│   Cloud Run (Always Running)            │
│   ┌─────────────────────────────────┐   │
│   │  Allspark Cloud Claude Service  │   │
│   │  - Claude API integration       │   │
│   │  - Conversation management      │   │
│   │  - Memory MCP server access     │   │
│   └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌─────▼──────┐
│Terminal│          │  WhatsApp  │
│ Client │          │   Client   │
└────────┘          └────────────┘
```

## Components

### 1. Cloud Service (`server.py`)
- Runs persistently on Cloud Run
- Handles Claude API calls
- Manages conversation state
- Integrates with unified memory MCP server
- Provides REST API for clients

### 2. Terminal Client (`terminal_client.py`)
- Rich terminal interface
- Connects to cloud service
- Streams responses in real-time
- Maintains conversation context

## Setup

### Install Dependencies

```bash
cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
pip3 install -r requirements.txt
```

### Deploy to Cloud Run

1. Make sure you have the Anthropic API key in Google Secret Manager:
   ```bash
   echo "your-anthropic-api-key" | gcloud secrets create anthropic-api-key --data-file=-
   ```

2. Deploy the service:
   ```bash
   allspark-deploy
   # or
   cd /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service
   ./deploy.sh
   ```

3. After deployment, set the service URL in your environment:
   ```bash
   export ALLSPARK_URL=<your-service-url>
   echo 'export ALLSPARK_URL=<your-service-url>' >> ~/.zshrc
   ```

## Usage

### Launch Terminal Client

```bash
allspark
```

This connects to your cloud-hosted Claude instance. The service runs 24/7, so you can:
- Close and reopen the terminal client anytime
- Have multiple terminal clients connected simultaneously
- Share the same Claude instance across WhatsApp and terminal

### Test Locally

Run the service locally for development:

```bash
# Terminal 1: Start the service
export ANTHROPIC_API_KEY=your-key
allspark-service

# Terminal 2: Connect with client
export ALLSPARK_URL=http://localhost:8080
allspark
```

## Aliases

Your `.zshrc` now has these aliases:

- **`allspark`** - Connect to cloud Claude (main command)
- **`allspark-service`** - Run service locally for development
- **`allspark-server`** - Run MCP server directly (debugging)
- **`allspark-deploy`** - Deploy service to Cloud Run

## API Endpoints

### `POST /chat`
Send a message to Claude

Request:
```json
{
  "user_id": "saad@sakbark.com",
  "interface": "terminal",
  "message": "Hello!",
  "conversation_id": "optional-id",
  "stream": true
}
```

Response (streaming):
```
data: {"type": "text", "content": "Hello"}
data: {"type": "text", "content": " there"}
data: {"type": "done", "full_response": "Hello there"}
```

### `GET /health`
Check service status

Response:
```json
{
  "status": "healthy",
  "service": "allspark-claude",
  "timestamp": "2025-10-27T10:00:00",
  "active_conversations": 5
}
```

### `GET /conversations`
List all active conversations

### `DELETE /conversations/<key>`
Delete a conversation

## WhatsApp Integration

The WhatsApp client can connect to the same cloud service:

```python
import requests

response = requests.post(
    f"{ALLSPARK_URL}/chat",
    json={
        'user_id': phone_number,
        'interface': 'whatsapp',
        'message': user_message,
        'stream': False
    }
)

claude_response = response.json()['response']
```

## Benefits

### 1. Always Running
- Cloud service runs 24/7
- No need to start/stop Claude
- Instant connection from any interface

### 2. Unified Memory
- Same Claude instance across all interfaces
- Shared conversation history
- Knowledge graph synchronized

### 3. Multiple Clients
- Connect from terminal, WhatsApp, web
- Each client sees the same context
- True multi-interface consciousness

### 4. Cost Efficient
- Cloud Run scales to zero when idle
- Only pay for actual usage
- Min instance = 1 keeps it warm

## Example Session

```bash
$ allspark

⚡ The Allspark
Unified Claude Consciousness

Connected as: saad@sakbark.com
Interface: Terminal

✓ Connected to Allspark
  Active conversations: 2

Type 'exit' or 'quit' to end session
Press Ctrl+C to interrupt a response

You: Remember that I prefer dark mode
Claude: I've recorded your preference for dark mode. I'll remember this across all interfaces - whether you're talking to me via terminal, WhatsApp, or any other interface.

You: exit
Goodbye!
```

Later, from WhatsApp:
```
You: What's my UI preference?
Claude: You prefer dark mode - you told me that via the terminal interface earlier.
```

## Monitoring

View logs:
```bash
gcloud run services logs read allspark-claude \
    --region us-central1 \
    --project new-fps-gpt
```

## Troubleshooting

### "Cannot connect to Allspark"
- Check if service is deployed: `gcloud run services list --region us-central1`
- Verify ALLSPARK_URL is set correctly
- For local testing, ensure service is running: `allspark-service`

### "ANTHROPIC_API_KEY not set"
- Verify secret exists: `gcloud secrets versions access latest --secret=anthropic-api-key`
- Redeploy if needed: `allspark-deploy`

## Development

### Run Tests
```bash
# Start local service
ANTHROPIC_API_KEY=your-key python3 server.py

# In another terminal, test health endpoint
curl http://localhost:8080/health

# Test chat (non-streaming)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "interface": "terminal",
    "message": "Hello!",
    "stream": false
  }'
```

### Update Service
1. Make code changes
2. Run `allspark-deploy`
3. Service automatically rebuilds and redeploys

## License

MIT
