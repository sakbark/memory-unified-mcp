#!/bin/bash
# Allspark Auto-Upgrade Script
# Automatically pulls latest changes and redeploys services

PROJECT_ID="new-fps-gpt"
REGION="us-central1"
REPO_DIR="/Users/saady/development/mcp-servers/memory-unified"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Allspark Auto-Upgrade System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$REPO_DIR"

# 1. Check for updates
echo -e "${BLUE}[1/4]${NC} Checking for updates..."

git fetch origin main

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✓${NC} Already up to date (commit: ${LOCAL:0:8})"
    exit 0
fi

echo -e "${YELLOW}ℹ${NC} Updates available:"
echo -e "  Local:  ${LOCAL:0:8}"
echo -e "  Remote: ${REMOTE:0:8}"
echo ""

# 2. Show changes
echo -e "${BLUE}[2/4]${NC} Changes to be applied:"
git log HEAD..origin/main --oneline --decorate

echo ""
read -p "Continue with upgrade? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

# 3. Pull updates
echo ""
echo -e "${BLUE}[3/4]${NC} Pulling updates..."

# Stash any local changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}ℹ${NC} Stashing local changes..."
    git stash
fi

git pull origin main

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Git pull failed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Updates pulled successfully"

# 4. Redeploy services
echo ""
echo -e "${BLUE}[4/4]${NC} Redeploying services..."

# Check what changed
CHANGED_FILES=$(git diff --name-only HEAD@{1} HEAD)

echo "Changed files:"
echo "$CHANGED_FILES"
echo ""

REDEPLOY_ALLSPARK=false
REDEPLOY_WHATSAPP=false

# Determine what needs redeployment
if echo "$CHANGED_FILES" | grep -q "cloud-claude-service/"; then
    REDEPLOY_ALLSPARK=true
fi

if echo "$CHANGED_FILES" | grep -q "whatsapp.*\.py\|main_thin_webhook"; then
    REDEPLOY_WHATSAPP=true
fi

# Redeploy Allspark if needed
if [ "$REDEPLOY_ALLSPARK" = true ]; then
    echo -e "${YELLOW}→${NC} Redeploying Allspark Cloud Claude..."

    cd "$REPO_DIR/cloud-claude-service"

    gcloud run deploy allspark-claude \
        --source . \
        --platform managed \
        --region $REGION \
        --project $PROJECT_ID \
        --quiet \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --min-instances 1 \
        --max-instances 10 \
        --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
        --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Allspark redeployed successfully"
    else
        echo -e "${RED}✗${NC} Allspark deployment failed"
        exit 1
    fi
else
    echo -e "${GREEN}ℹ${NC} Allspark deployment not needed"
fi

# Redeploy WhatsApp if needed
if [ "$REDEPLOY_WHATSAPP" = true ]; then
    echo -e "${YELLOW}→${NC} Redeploying WhatsApp webhook..."

    cd /Users/saady/whatsapp-claude-webhook

    # Deploy the main webhook
    gcloud run deploy whatsapp-claude-webhook \
        --source . \
        --platform managed \
        --region $REGION \
        --project $PROJECT_ID \
        --quiet \
        --memory 512Mi \
        --timeout 300 \
        --max-instances 10 \
        --min-instances 0 \
        --set-env-vars PROJECT_ID=$PROJECT_ID,ALLSPARK_URL=https://allspark-claude-958443682078.us-central1.run.app

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} WhatsApp webhook redeployed successfully"
    else
        echo -e "${RED}✗${NC} WhatsApp deployment failed"
        exit 1
    fi
else
    echo -e "${GREEN}ℹ${NC} WhatsApp deployment not needed"
fi

# 5. Verify health
echo ""
echo -e "${BLUE}Verifying health...${NC}"
sleep 5

HEALTH=$(curl -s https://allspark-claude-958443682078.us-central1.run.app/health)

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Allspark is healthy"
else
    echo -e "${YELLOW}⚠${NC} Health check inconclusive"
fi

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Upgrade Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "New version: $(git rev-parse --short HEAD)"
echo ""
echo "Test with:"
echo "  allspark"
