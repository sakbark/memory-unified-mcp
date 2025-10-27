#!/bin/bash
# Launch Allspark Terminal Client
# Connects to cloud-hosted Claude instance with unified memory

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if ALLSPARK_URL is set
if [ -z "$ALLSPARK_URL" ]; then
    echo -e "${YELLOW}⚠ ALLSPARK_URL not set${NC}"
    echo -e "${YELLOW}Using local service: http://localhost:8080${NC}"
    echo -e "${YELLOW}To use cloud service, set: export ALLSPARK_URL=<your-cloud-url>${NC}"
    export ALLSPARK_URL="http://localhost:8080"
fi

echo -e "${BLUE}⚡ Launching Allspark Terminal Client...${NC}"
echo -e "${GREEN}Connecting to: $ALLSPARK_URL${NC}"

# Navigate to the directory
cd /Users/saady/development/mcp-servers/memory-unified

# Launch the terminal client
python3 cloud-claude-service/terminal_client.py
