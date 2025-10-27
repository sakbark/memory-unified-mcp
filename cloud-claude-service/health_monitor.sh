#!/bin/bash
# Allspark Health Monitor & Auto-Repair System
# Ensures Allspark Cloud Claude is always running and healthy

PROJECT_ID="new-fps-gpt"
SERVICE_NAME="allspark-claude"
REGION="us-central1"
SERVICE_URL="https://allspark-claude-958443682078.us-central1.run.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_health() {
    log_info "Checking Allspark health..."

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL/health" 2>/dev/null)

    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Allspark is healthy (HTTP $HTTP_CODE)"
        return 0
    else
        log_error "Allspark health check failed (HTTP $HTTP_CODE)"
        return 1
    fi
}

check_service_status() {
    log_info "Checking Cloud Run service status..."

    STATUS=$(gcloud run services describe $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --format='value(status.conditions[0].status)' 2>/dev/null)

    if [ "$STATUS" = "True" ]; then
        log_success "Cloud Run service is running"
        return 0
    else
        log_error "Cloud Run service status: $STATUS"
        return 1
    fi
}

restart_service() {
    log_warning "Attempting to restart service..."

    # Update with no-traffic to force a new revision
    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --no-traffic \
        --quiet 2>&1 > /dev/null

    sleep 5

    # Route all traffic back
    gcloud run services update-traffic $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --to-latest \
        --quiet 2>&1 > /dev/null

    log_info "Waiting 30 seconds for service to stabilize..."
    sleep 30
}

scale_up() {
    log_warning "Ensuring minimum instances..."

    gcloud run services update $SERVICE_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --min-instances 1 \
        --quiet 2>&1 > /dev/null

    log_info "Waiting 20 seconds for scale-up..."
    sleep 20
}

repair_sequence() {
    log_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_warning "Starting auto-repair sequence..."
    log_warning "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Step 1: Check service status
    if ! check_service_status; then
        log_error "Service is not running properly"

        # Step 2: Try scaling up
        scale_up

        if check_health; then
            log_success "✓ Service recovered after scale-up"
            return 0
        fi

        # Step 3: Try restart
        restart_service

        if check_health; then
            log_success "✓ Service recovered after restart"
            return 0
        fi

        log_error "✗ Auto-repair failed - manual intervention required"
        return 1
    fi

    # If service status is good but health check fails
    log_warning "Service status is OK but health check failed"
    log_warning "This might be a temporary issue, waiting 30s..."
    sleep 30

    if check_health; then
        log_success "✓ Service recovered"
        return 0
    fi

    # Try restart as last resort
    restart_service

    if check_health; then
        log_success "✓ Service recovered after restart"
        return 0
    fi

    log_error "✗ Auto-repair failed - manual intervention required"
    return 1
}

send_notification() {
    local status=$1
    local message=$2

    # Log to file
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $status: $message" >> /tmp/allspark_monitor.log

    # TODO: Add Slack/email notification here if needed
}

monitor_once() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Allspark Health Check - $(date)"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if check_health; then
        log_success "✓ All systems operational"
        send_notification "HEALTHY" "Allspark is running normally"
        return 0
    else
        log_error "✗ Health check failed"
        send_notification "UNHEALTHY" "Allspark health check failed, starting repair"

        if repair_sequence; then
            send_notification "RECOVERED" "Allspark auto-repair succeeded"
            return 0
        else
            send_notification "FAILED" "Allspark auto-repair failed - manual intervention needed"
            return 1
        fi
    fi
}

continuous_monitor() {
    log_info "Starting continuous health monitoring..."
    log_info "Checking every 60 seconds"
    log_info "Press Ctrl+C to stop"
    echo ""

    while true; do
        monitor_once
        log_info "Next check in 60 seconds..."
        sleep 60
    done
}

show_usage() {
    echo "Usage: $0 [once|continuous|status]"
    echo ""
    echo "Commands:"
    echo "  once       - Run health check once and repair if needed"
    echo "  continuous - Run continuous monitoring (every 60s)"
    echo "  status     - Show current service status"
    echo ""
}

# Main
case "${1:-once}" in
    once)
        monitor_once
        ;;
    continuous)
        continuous_monitor
        ;;
    status)
        check_service_status
        check_health
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
