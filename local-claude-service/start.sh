#!/bin/bash
# Start Local Claude Service with proper environment

cd "$(dirname "$0")"

# Get API key from Secret Manager
export LOCAL_CLAUDE_API_KEY=$(gcloud secrets versions access latest --secret=local-claude-api-key --project=new-fps-gpt 2>/dev/null || echo "dev-key-changeme")
export ANTHROPIC_API_KEY=$(gcloud secrets versions access latest --secret=anthropic-api-key --project=new-fps-gpt 2>/dev/null)

echo "Starting Local Claude Service..."
echo "API Key: ${LOCAL_CLAUDE_API_KEY:0:10}..."

python3 server.py
