#!/bin/bash
# Daily Allspark Backup Script
# Backs up Firestore data, configuration, and pushes to GitHub

PROJECT_ID="new-fps-gpt"
BACKUP_DIR="/Users/saady/allspark-backups"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Allspark Daily Backup - $DATE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"
cd "$BACKUP_DIR/$DATE"

echo -e "${GREEN}✓${NC} Backup directory: $BACKUP_DIR/$DATE"

# 1. Backup Firestore
echo ""
echo -e "${BLUE}[1/5]${NC} Backing up Firestore data..."

FIRESTORE_BACKUP_NAME="allspark-firestore-$TIMESTAMP"
FIRESTORE_BUCKET="gs://new-fps-gpt-firestore-backups"

# Create bucket if it doesn't exist
gsutil mb -p $PROJECT_ID $FIRESTORE_BUCKET 2>/dev/null || true

# Export Firestore
gcloud firestore export "$FIRESTORE_BUCKET/$FIRESTORE_BACKUP_NAME" \
    --project=$PROJECT_ID \
    --async 2>&1 | tee firestore_export.log

echo -e "${GREEN}✓${NC} Firestore export initiated: $FIRESTORE_BACKUP_NAME"

# 2. Backup service configurations
echo ""
echo -e "${BLUE}[2/5]${NC} Backing up service configurations..."

# Allspark Cloud Claude config
gcloud run services describe allspark-claude \
    --region us-central1 \
    --project $PROJECT_ID \
    --format=yaml > allspark-claude-config.yaml

# WhatsApp webhook config
gcloud run services describe whatsapp-claude-webhook \
    --region us-central1 \
    --project $PROJECT_ID \
    --format=yaml > whatsapp-claude-webhook-config.yaml

echo -e "${GREEN}✓${NC} Service configurations saved"

# 3. Backup codebase to GitHub
echo ""
echo -e "${BLUE}[3/5]${NC} Backing up codebase to GitHub..."

cd /Users/saady/development/mcp-servers/memory-unified

# Check for changes
if [[ -n $(git status -s) ]]; then
    git add -A
    git commit -m "Daily backup - $DATE

- Auto backup of Allspark system
- Firestore export: $FIRESTORE_BACKUP_NAME
- Service configs saved
" 2>&1 | tee -a "$BACKUP_DIR/$DATE/git_backup.log"

    git push origin main 2>&1 | tee -a "$BACKUP_DIR/$DATE/git_backup.log"
    echo -e "${GREEN}✓${NC} Code pushed to GitHub"
else
    echo -e "${YELLOW}ℹ${NC} No code changes to backup"
fi

# 4. Create backup manifest
echo ""
echo -e "${BLUE}[4/5]${NC} Creating backup manifest..."

cat > "$BACKUP_DIR/$DATE/manifest.txt" <<EOF
Allspark Backup Manifest
========================
Date: $DATE
Timestamp: $TIMESTAMP

Services:
---------
Allspark Cloud Claude: https://allspark-claude-958443682078.us-central1.run.app
WhatsApp Claude Webhook: https://whatsapp-claude-webhook-np7c3nmqfa-uc.a.run.app

Firestore Backup:
-----------------
Bucket: $FIRESTORE_BUCKET
Export: $FIRESTORE_BACKUP_NAME
Location: $FIRESTORE_BUCKET/$FIRESTORE_BACKUP_NAME

Service Configs:
----------------
$(ls -lh *.yaml 2>/dev/null || echo "No config files")

Git Commit:
-----------
$(git log -1 --pretty=format:"Commit: %H%nDate: %ad%nMessage: %s" 2>/dev/null || echo "No git info")

Health Status:
--------------
$(curl -s https://allspark-claude-958443682078.us-central1.run.app/health 2>/dev/null || echo "Could not check health")
EOF

echo -e "${GREEN}✓${NC} Manifest created"

# 5. Cleanup old backups (keep last 30 days)
echo ""
echo -e "${BLUE}[5/5]${NC} Cleaning up old backups..."

find "$BACKUP_DIR" -type d -name "20*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

echo -e "${GREEN}✓${NC} Old backups cleaned (kept last 30 days)"

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Backup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Backup location: $BACKUP_DIR/$DATE"
echo "Firestore backup: $FIRESTORE_BUCKET/$FIRESTORE_BACKUP_NAME"
echo ""
echo "To restore Firestore:"
echo "  gcloud firestore import $FIRESTORE_BUCKET/$FIRESTORE_BACKUP_NAME --project=$PROJECT_ID"
