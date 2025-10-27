#!/bin/bash
# Launch Allspark Claude - A Claude instance with unified memory enabled
# This creates a Claude session that can share memory across all interfaces

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚡ Launching Allspark Claude...${NC}"
echo -e "${GREEN}This Claude instance uses unified memory across all interfaces${NC}\n"

# Set environment variables for the MCP server
export GOOGLE_CLOUD_PROJECT="new-fps-gpt"
export MCP_SERVER_PATH="/Users/saady/development/mcp-servers/memory-unified/server.py"

# Create a temporary Claude config that includes the memory-unified MCP server
TEMP_CONFIG=$(mktemp)
cat > "$TEMP_CONFIG" << 'EOF'
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
EOF

echo -e "${YELLOW}Memory server configured at: $MCP_SERVER_PATH${NC}"
echo -e "${YELLOW}Using project: $GOOGLE_CLOUD_PROJECT${NC}\n"
echo -e "${GREEN}Starting Claude with unified memory...${NC}\n"

# Launch Claude CLI with the memory server config
# Note: The claude command should pick up MCP servers from the config
claude --config "$TEMP_CONFIG"

# Cleanup
rm "$TEMP_CONFIG"
