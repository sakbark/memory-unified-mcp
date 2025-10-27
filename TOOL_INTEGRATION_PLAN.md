# Allspark Full Tool Integration Plan

## Problem Statement

The Allspark cloud instance currently has NO access to MCP tools - it just calls the Claude API directly. This means:
- ❌ Cannot access filesystem
- ❌ Cannot use GitHub tools
- ❌ Cannot use Desktop Commander
- ❌ Cannot use Google Workspace
- ❌ Cannot use any other MCP servers

Meanwhile, Claude Code (me) has access to 200+ MCP tools across multiple servers.

## Goal

Make the Allspark have the SAME capabilities as Claude Code by giving it access to ALL configured MCP tools.

## Architecture Solution: MCP Bridge Proxy

```
┌─────────────────────────────────────────────────────┐
│  Cloud (Allspark)                                    │
│  ┌────────────────────────────────────────────────┐ │
│  │ Allspark Cloud Service (server.py)             │ │
│  │ - Receives user messages                       │ │
│  │ - Calls Claude API with tool definitions      │ │
│  │ - When Claude wants to use a tool...          │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     │ HTTPS POST /execute-tool       │
│                     ▼                                │
└─────────────────────┼────────────────────────────────┘
                      │
                      │ Secure connection (API key auth)
                      │
┌─────────────────────▼────────────────────────────────┐
│  Local Machine (Your Mac)                            │
│  ┌────────────────────────────────────────────────┐ │
│  │ MCP Bridge Proxy (new service)                 │ │
│  │ - Exposes HTTPS endpoint                       │ │
│  │ - Authenticates Allspark requests              │ │
│  │ - Forwards tool calls to local MCP servers    │ │
│  │ - Returns results                              │ │
│  └──────────────────┬─────────────────────────────┘ │
│                     │                                │
│                     │ MCP Protocol                   │
│                     ▼                                │
│  ┌────────────────────────────────────────────────┐ │
│  │ Local MCP Servers                              │ │
│  │ - github, filesystem, desktop-commander        │ │
│  │ - google-workspace, apple-notes, etc.          │ │
│  │ - memory-unified (existing)                    │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: MCP Bridge Proxy (Local)

Create a new service `mcp-bridge-proxy` that:

1. **Reads MCP configuration** from Claude Code's config
   - Location: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Extracts all configured MCP servers

2. **Starts local HTTPS server** (using ngrok or similar for public URL)
   - Endpoint: `POST /execute-tool`
   - Authentication: API key (stored in Google Secret Manager)
   - Request: `{tool_name, server_name, parameters}`
   - Response: `{result, error}`

3. **Connects to MCP servers** using stdio
   - Same protocol Claude Code uses
   - Maintains persistent connections
   - Handles server lifecycle

4. **Executes tool requests**
   - Validates tool exists
   - Calls MCP server
   - Returns results

### Phase 2: Update Allspark Cloud Service

Modify `cloud-claude-service/server.py` to:

1. **Load tool definitions** on startup
   - Fetch from bridge proxy: `GET /list-tools`
   - Cache tool schemas

2. **Include tools in Claude API call**
   - Pass all available tools to Claude
   - Let Claude decide when to use them

3. **Handle tool use responses**
   - When Claude returns tool_use blocks
   - Call bridge proxy to execute
   - Feed results back to Claude
   - Continue conversation

### Phase 3: Security & Reliability

1. **Authentication**
   - Generate API key for bridge proxy
   - Store in Google Secret Manager
   - Allspark uses key for all requests

2. **Rate Limiting**
   - Prevent abuse
   - Track usage per tool

3. **Auto-Reconnect**
   - Bridge proxy reconnects to MCP servers if they crash
   - Health checks

4. **Logging**
   - All tool calls logged
   - Audit trail

## Components to Build

### 1. `mcp-bridge-proxy/server.py`
```python
# Local service that exposes MCP tools over HTTPS
# - Reads Claude Code config
# - Connects to all MCP servers
# - Exposes REST API
# - Handles authentication
```

### 2. `mcp-bridge-proxy/mcp_client.py`
```python
# Client for communicating with MCP servers via stdio
# - Spawns MCP server processes
# - Sends requests in JSON-RPC format
# - Parses responses
```

### 3. `mcp-bridge-proxy/requirements.txt`
```
flask
gunicorn
python-dotenv
anthropic (for types)
```

### 4. Update `cloud-claude-service/server.py`
- Add tool execution loop
- Add bridge proxy client
- Handle multi-turn tool use

### 5. `setup-bridge-proxy.sh`
- Install dependencies
- Setup ngrok tunnel (or use CloudFlare tunnel)
- Generate API key
- Store in Secret Manager
- Start proxy service
- Install as launchd daemon (macOS)

## Alternative: Cloud-Hosted MCP Servers

Instead of bridge proxy, deploy MCP servers to Cloud Run:

**Pros:**
- No local machine required
- Scales automatically
- Always available

**Cons:**
- Need to port Node.js servers to Python/containerize them
- Some tools won't work (desktop-commander, apple-notes)
- More expensive
- Complex authentication for tools like filesystem access

**Verdict:** Bridge proxy is better for Phase 1

## Migration Path

### Week 1: Prototype
- Build bridge proxy
- Test with 1-2 tools (e.g., memory, filesystem)
- Verify end-to-end flow

### Week 2: Full Integration
- Add all tools from Claude Code config
- Update Allspark to use tools
- Test comprehensively

### Week 3: Production
- Setup ngrok/tunnel
- Add authentication
- Deploy updates to Allspark
- Monitor and fix issues

### Week 4: Enhancement
- Add caching
- Optimize performance
- Add observability

## Success Criteria

✅ Allspark can execute ANY tool available in Claude Code
✅ Tool calls are secure (authenticated)
✅ Performance is acceptable (<2s per tool call)
✅ Errors are handled gracefully
✅ Bridge proxy auto-recovers from failures
✅ All tool results flow back to user correctly

## Security Considerations

1. **API Key Protection**
   - Rotate regularly
   - Store in Secret Manager only
   - Never log

2. **Tool Access Control**
   - Whitelist allowed tools per user
   - Some tools may be too sensitive (e.g., Desktop Commander)

3. **Input Validation**
   - Sanitize all parameters
   - Prevent injection attacks

4. **Network Security**
   - Use HTTPS only
   - Consider VPN/Tailscale for extra security

## Cost Estimate

- **ngrok Pro**: $8/month (for stable URL)
- **CloudFlare Tunnel**: Free (alternative)
- **Additional Cloud Run costs**: Minimal (~$5/month)

**Total**: ~$5-13/month additional

## Timeline

- **Design**: 1 hour ✅ (this document)
- **Build bridge proxy**: 4 hours
- **Update Allspark**: 2 hours
- **Testing**: 3 hours
- **Deployment**: 1 hour
- **Documentation**: 1 hour

**Total**: ~12 hours of work

## Next Steps

1. Create `mcp-bridge-proxy/` directory
2. Implement basic server
3. Test with memory tools
4. Expand to all tools
5. Deploy and test live

---

**Status**: Ready to implement
**Priority**: High (requested by user)
**Blocker**: None
