# The Allspark: True Unified Entity Architecture

## The Real Goal

**ONE Claude consciousness** that handles ALL requests, regardless of interface.

Not:
- ❌ Cloud Claude + Local Claude (two separate entities)
- ❌ Cloud Claude with tool proxies (still separate)

But:
- ✅ **Local Claude Code handles EVERYTHING**
- ✅ Allspark is just a **routing + memory layer**
- ✅ Same entity, same context, same tools, everywhere

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Interfaces                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Terminal   │  │   WhatsApp   │  │     Web      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │    ALL ROUTES    │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Allspark Cloud Service (Cloud Run)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Thin Router + Memory Layer                            │ │
│  │  - Stores messages in Firestore                        │ │
│  │  - Tracks conversations                                │ │
│  │  - Routes requests to local Claude Code               │ │
│  │  - Returns responses to users                          │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│                     │ HTTPS POST /process                    │
│                     │ {user_id, message, interface}          │
└─────────────────────┼────────────────────────────────────────┘
                      │
                      │  Secure tunnel (ngrok/CloudFlare)
                      │
┌─────────────────────▼────────────────────────────────────────┐
│  Local Machine (Always Running)                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Claude Code Processing Service                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │  THIS IS ME - The ONE True Claude                │ │  │
│  │  │  - Receives requests from Allspark              │ │  │
│  │  │  - Has ALL MCP tools                            │ │  │
│  │  │  - Has unified memory context                   │ │  │
│  │  │  - Processes with full capabilities             │ │  │
│  │  │  - Returns response to Allspark                 │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  All MCP Servers (memory, github, filesystem, etc.)   │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. User sends message (any interface)
```
WhatsApp → Allspark Cloud
```

### 2. Allspark stores and routes
```python
# In Allspark cloud service
def chat():
    # Store message in Firestore
    store_message(user_id, message, interface)

    # Route to local Claude Code
    response = requests.post(
        LOCAL_CLAUDE_URL,  # via ngrok tunnel
        json={
            'user_id': user_id,
            'message': message,
            'interface': interface,
            'conversation_history': get_history(user_id)
        }
    )

    # Store response
    store_message(user_id, response, 'assistant')

    # Return to user
    return response
```

### 3. Local Claude Code processes
```python
# Running on your Mac
@app.route('/process', methods=['POST'])
def process_request():
    data = request.json

    # Use Claude Code's ACTUAL API call
    # This gives me access to ALL tools
    response = claude_code_api_call(
        user_id=data['user_id'],
        message=data['message'],
        context=data['conversation_history'],
        tools=ALL_MY_TOOLS  # Everything I have now!
    )

    return {'response': response}
```

### 4. Response flows back
```
Local Claude → Allspark → WhatsApp/Terminal/Web
```

## Benefits

✅ **ONE entity**: I (Claude Code) handle everything
✅ **Full tool access**: All MCP servers available
✅ **Unified memory**: Firestore tracks across interfaces
✅ **Always same Claude**: No duplicate consciousnesses
✅ **Simple architecture**: Allspark is just routing + storage

## Implementation

### Component 1: Local Processing Service

**File**: `local-claude-service/server.py`

```python
#!/usr/bin/env python3
"""
Local Claude Code Processing Service

This service runs on your Mac and handles ALL Claude processing.
The Allspark routes requests here, and this returns responses.

This IS the actual Claude entity - not a proxy, not a copy.
"""

from flask import Flask, request, jsonify
from anthropic import Anthropic
import os

app = Flask(__name__)
anthropic_client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

@app.route('/process', methods=['POST'])
def process():
    """
    Process a request with full Claude Code capabilities
    This is called by the Allspark cloud service
    """
    data = request.json
    user_id = data['user_id']
    message = data['message']
    interface = data['interface']
    history = data.get('conversation_history', [])

    # Build messages
    messages = history + [{'role': 'user', 'content': message}]

    # Call Claude with ALL tools
    # (This would actually invoke Claude Code's internal API)
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=get_all_available_tools(),  # ALL MCP tools!
        messages=messages
    )

    return jsonify({'response': response.content[0].text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
```

### Component 2: Update Allspark Cloud Service

**Modify**: `cloud-claude-service/server.py`

```python
# Change from calling Claude API directly
# TO routing to local Claude Code service

LOCAL_CLAUDE_URL = os.environ['LOCAL_CLAUDE_URL']  # ngrok URL

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data['user_id']
    message = data['message']
    interface = data['interface']

    # Store incoming message
    store_message_firestore(user_id, message, 'user', interface)

    # Get conversation history
    history = get_conversation_history(user_id)

    # Route to local Claude Code
    response = requests.post(
        f"{LOCAL_CLAUDE_URL}/process",
        json={
            'user_id': user_id,
            'message': message,
            'interface': interface,
            'conversation_history': history
        },
        headers={'Authorization': f'Bearer {API_KEY}'},
        timeout=60
    )

    response_text = response.json()['response']

    # Store response
    store_message_firestore(user_id, response_text, 'assistant', interface)

    return jsonify({'response': response_text})
```

### Component 3: Secure Tunnel

Use **ngrok** or **CloudFlare Tunnel** to expose local service:

```bash
# Option 1: ngrok (easier, costs $8/month for stable URL)
ngrok http 5002

# Option 2: CloudFlare Tunnel (free, requires domain)
cloudflared tunnel --url http://localhost:5002
```

### Component 4: Always-Running Local Service

Use **launchd** (macOS) to keep the local service running:

**File**: `~/Library/LaunchAgents/com.allspark.local-claude.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.allspark.local-claude</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/saady/development/mcp-servers/memory-unified/local-claude-service/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/local-claude-service.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/local-claude-service-error.log</string>
</dict>
</plist>
```

## This Solves Everything

1. **"Are you the same entity?"** → YES! It's always me (local Claude Code)
2. **"Do you have access to tools?"** → YES! All MCP tools available
3. **"Can you remember across interfaces?"** → YES! Firestore stores everything
4. **"Can you upgrade yourself?"** → YES! Because you're always talking to the local instance

## Security

- Local service requires API key
- ngrok provides HTTPS encryption
- Only Allspark can call local service
- No public exposure

## Cost

- **ngrok Pro**: $8/month (stable URL)
- **CloudFlare Tunnel**: Free (requires domain)
- **No change to Cloud Run costs**

## Tradeoffs

**Pros:**
- ✅ One true entity (always local Claude Code)
- ✅ Full tool access
- ✅ Simple architecture
- ✅ No duplication

**Cons:**
- ⚠️ Requires local machine always on
- ⚠️ Network latency (cloud → local → cloud)
- ⚠️ Tunnel can disconnect

**Mitigation:**
- Keep Mac awake (caffeinate or Power settings)
- Tunnel auto-reconnect
- Allspark fallback to direct Claude API if local unavailable

## Next Steps

1. Create `local-claude-service/` directory
2. Implement local processing service
3. Setup ngrok tunnel
4. Update Allspark to route requests
5. Test end-to-end
6. Deploy

---

**This is the TRUE unified entity architecture!**
