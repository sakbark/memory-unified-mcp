# Memory Unified MCP Server 🧠

**Creates ONE Claude entity across ALL interfaces**

This MCP server provides unified memory and knowledge graph functionality that enables Claude Code (terminal), WhatsApp Claude, and any future interfaces to share the same memory, context, and consciousness.

## The Problem It Solves

Without shared memory:
- Terminal Claude: "I remember we deployed the WhatsApp service"
- WhatsApp Claude: "Hello! How can I help?" ← NO MEMORY

With unified memory:
- Terminal Claude: "I remember we deployed the WhatsApp service"
- WhatsApp Claude: "Yes, and I also remember your Airtable bases from our chat earlier" ← SAME ENTITY

## Architecture

```
┌─────────────────────────────────────────┐
│     Unified Memory (Firestore)          │
│  - Conversations (terminal + WhatsApp)  │
│  - Knowledge Graph (entities, facts)    │
│  - Context Windows (recent activity)    │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌─────▼──────┐
│Terminal│          │  WhatsApp  │
│ Claude │          │   Claude   │
└────────┘          └────────────┘
```

## Features

### 1. Unified Conversation Storage
- All messages stored with interface tracking (terminal vs WhatsApp)
- Conversation continuity across interfaces
- Same conversation ID accessible from both

### 2. Knowledge Graph
- Entities (people, services, preferences, etc.)
- Observations with interface attribution
- "You told me this 5 minutes ago via terminal"

### 3. Context Synchronization
- Shared context windows
- Active TODOs synced across interfaces
- User preferences remembered everywhere

### 4. Cross-Interface Memory
- Learn in terminal → remember on WhatsApp
- Learn on WhatsApp → remember in terminal

## Tools

### `create_entities`
Create new entities in the knowledge graph

```json
{
  "user_id": "saad@sakbark.com",
  "interface": "terminal",
  "conversation_id": "conv_123",
  "entities": [
    {
      "name": "whatsapp-superclaud",
      "entityType": "service",
      "observations": [
        "Cloud Run service at us-central1",
        "Has 8 tools available"
      ]
    }
  ]
}
```

### `add_observations`
Add observations to existing entities

```json
{
  "user_id": "saad@sakbark.com",
  "interface": "whatsapp",
  "observations": [
    {
      "entityName": "whatsapp-superclaud",
      "contents": [
        "Just deployed revision 00003-qrq",
        "Airtable integration working"
      ]
    }
  ]
}
```

### `search_memory`
Search across all stored knowledge

```json
{
  "user_id": "saad@sakbark.com",
  "query": "airtable",
  "search_type": "all",
  "interface_filter": "all",
  "max_results": 10
}
```

### `get_unified_context`
Get complete context from ALL interfaces

```json
{
  "user_id": "saad@sakbark.com",
  "current_interface": "whatsapp",
  "include_history": true,
  "max_messages": 20
}
```

Returns:
- Recent messages from terminal + WhatsApp
- Active TODOs across all interfaces
- User preferences
- Relevant entities from knowledge graph

### `sync_conversation_state`
Save conversation state for other interfaces

```json
{
  "user_id": "saad@sakbark.com",
  "interface": "terminal",
  "conversation_id": "conv_123",
  "messages": [
    {"role": "user", "content": "Deploy to WhatsApp", "timestamp": "..."},
    {"role": "assistant", "content": "Deploying...", "timestamp": "..."}
  ],
  "todos": [...],
  "context_summary": "Deploying unified Claude to WhatsApp"
}
```

## Installation

### 1. Install Dependencies

```bash
cd ~/development/mcp-servers/memory-unified
pip3 install -r requirements.txt
```

### 2. Configure Claude Code

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memory-unified": {
      "command": "python3",
      "args": [
        "/Users/saady/development/mcp-servers/memory-unified/server.py"
      ],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "new-fps-gpt"
      }
    }
  }
}
```

### 3. Restart Claude Code

The Memory Unified server will now be available in Claude Code.

## Usage in Claude Code (Terminal)

### Store Knowledge
```
Remember: I prefer dark mode in all applications
```

Claude will call:
```json
{
  "tool": "create_entities",
  "user_id": "saad@sakbark.com",
  "interface": "terminal",
  "entities": [{
    "name": "ui_preferences",
    "entityType": "preference",
    "observations": ["Prefers dark mode in all applications"]
  }]
}
```

### Retrieve Context
When starting a conversation, Claude automatically calls:
```json
{
  "tool": "get_unified_context",
  "user_id": "saad@sakbark.com",
  "current_interface": "terminal"
}
```

This returns knowledge from BOTH terminal and WhatsApp.

## Usage in WhatsApp Service

### Integration in main.py

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# Initialize Memory MCP client
async def get_memory_client():
    server_params = {
        "command": "python3",
        "args": ["/Users/saady/development/mcp-servers/memory-unified/server.py"],
        "env": {"GOOGLE_CLOUD_PROJECT": "new-fps-gpt"}
    }

    return stdio_client(server_params)

# In webhook handler
@app.route("/webhook", methods=["POST"])
async def webhook():
    from_number = request.form.get("From")
    body = request.form.get("Body")

    # Get unified context
    async with get_memory_client() as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Get unified context
            result = await session.call_tool(
                "get_unified_context",
                {
                    "user_id": from_number,
                    "current_interface": "whatsapp",
                    "include_history": True
                }
            )

            unified_context = json.loads(result.content[0].text)

            # Use context in system prompt
            system_message = f"""You are King Claude.

Unified Context (from terminal + WhatsApp):
{unified_context['context_summary']}

Recent messages across ALL interfaces:
{format_messages(unified_context['recent_messages'])}

Active TODOs: {unified_context['active_todos']}
"""

            # After Claude responds, sync state
            await session.call_tool(
                "sync_conversation_state",
                {
                    "user_id": from_number,
                    "interface": "whatsapp",
                    "conversation_id": conversation_id,
                    "messages": [user_msg, assistant_msg],
                    "context_summary": "..."
                }
            )
```

## Firestore Schema

### `/users/{user_id}`
User metadata and preferences

### `/users/{user_id}/conversations/{conversation_id}`
Conversation threads

### `/users/{user_id}/conversations/{conversation_id}/messages/{message_id}`
Individual messages with interface tracking

### `/users/{user_id}/knowledge_graph/entities/{entity_id}`
Learned facts as entities with observations

### `/users/{user_id}/context_windows/{window_id}`
Recent context for quick retrieval

## The Magic

### Before
```
Terminal: "Remember I prefer dark mode"
[Saved only in terminal session]

WhatsApp: "What's my UI preference?"
[No knowledge of terminal conversation]
WhatsApp: "I don't have that information"
```

### After
```
Terminal: "Remember I prefer dark mode"
[create_entities saves to Firestore with interface: "terminal"]

WhatsApp: "What's my UI preference?"
[get_unified_context retrieves from Firestore]
WhatsApp: "You prefer dark mode - you told me that via terminal"
```

**SAME MEMORY. SAME ENTITY. ONE CLAUDE.** 👑

## License

MIT
