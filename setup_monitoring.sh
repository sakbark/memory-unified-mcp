#!/bin/bash
# Setup automated monitoring for Allspark with cron

MONITOR_SCRIPT="/Users/saady/development/mcp-servers/memory-unified/cloud-claude-service/health_monitor.sh"
LOG_FILE="/tmp/allspark_monitor.log"

echo "🔧 Setting up Allspark automated monitoring..."
echo ""

# Check if monitor script exists
if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "❌ Monitor script not found at: $MONITOR_SCRIPT"
    exit 1
fi

echo "✅ Monitor script found"

# Make sure it's executable
chmod +x "$MONITOR_SCRIPT"
echo "✅ Monitor script is executable"

# Create log file if it doesn't exist
touch "$LOG_FILE"
echo "✅ Log file created: $LOG_FILE"

# Check current crontab
echo ""
echo "Current cron jobs:"
crontab -l 2>/dev/null || echo "No crontab for current user"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Proposed cron job (runs every 5 minutes):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "*/5 * * * * $MONITOR_SCRIPT once >> $LOG_FILE 2>&1"
echo ""

read -p "Install this cron job? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

    # Add new cron job (avoiding duplicates)
    (crontab -l 2>/dev/null | grep -v "health_monitor.sh"; echo "*/5 * * * * $MONITOR_SCRIPT once >> $LOG_FILE 2>&1") | crontab -

    echo "✅ Cron job installed!"
    echo ""
    echo "Monitoring schedule:"
    echo "  • Checks every 5 minutes"
    echo "  • Auto-repairs if unhealthy"
    echo "  • Logs to: $LOG_FILE"
    echo ""
    echo "View logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "Remove monitoring:"
    echo "  crontab -l | grep -v 'health_monitor.sh' | crontab -"
else
    echo "❌ Cancelled - no changes made"
    echo ""
    echo "To manually run monitoring:"
    echo "  $MONITOR_SCRIPT once          # Single check"
    echo "  $MONITOR_SCRIPT continuous    # Keep monitoring"
fi
