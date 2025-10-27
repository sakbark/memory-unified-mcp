# Allspark Comprehensive Test Plan

## Overview
This document outlines every test to verify Allspark is fully operational with all features and permissions.

## Pre-Test Verification
- [ ] Services deployed to Cloud Run
- [ ] Environment variables configured (ALLSPARK_URL)
- [ ] Authentication configured (saad@sakbark.com)
- [ ] All secrets in Google Secret Manager

## Test Suite

### Test 1: Service Health Checks ✓
**Objective**: Verify both services are deployed and responding

**Steps**:
1. Check Allspark Cloud Claude health
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/health
   ```
   Expected: HTTP 200, status: "healthy"

2. Check WhatsApp webhook health
   ```bash
   curl https://whatsapp-superclaud-958443682078.us-central1.run.app/health
   ```
   Expected: HTTP 200, status: "healthy", allspark_url present

3. Verify Cloud Run services
   ```bash
   gcloud run services list --region us-central1 --project new-fps-gpt
   ```
   Expected: Both services listed and "READY"

**Pass Criteria**: All endpoints return 200, services show as READY

---

### Test 2: Terminal Client Connection
**Objective**: Verify terminal client can connect to cloud Claude

**Steps**:
1. Verify ALLSPARK_URL is set
   ```bash
   echo $ALLSPARK_URL
   ```
   Expected: https://allspark-claude-958443682078.us-central1.run.app

2. Launch terminal client
   ```bash
   allspark
   ```
   Expected: Connection successful, shows "Connected to Allspark"

3. Send test message
   ```
   You: Hello, are you operational?
   ```
   Expected: Claude responds appropriately

4. Exit cleanly
   ```
   You: exit
   ```
   Expected: Graceful shutdown

**Pass Criteria**: Client connects, exchanges messages, exits cleanly

---

### Test 3: Memory Storage
**Objective**: Verify Claude can store facts to unified memory

**Steps**:
1. Store multiple facts via terminal
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "saad@sakbark.com",
       "interface": "terminal",
       "message": "Remember these facts: 1) My favorite color is blue 2) I prefer TypeScript 3) I work at Sakbark",
       "stream": false
     }'
   ```
   Expected: Claude acknowledges storing the facts

2. Check conversation was saved
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/conversations
   ```
   Expected: Shows conversation with saad@sakbark.com

3. Verify Firestore storage
   ```bash
   gcloud firestore collections list --project=new-fps-gpt
   ```
   Expected: Shows "users" collection

**Pass Criteria**: Facts stored, conversation tracked, Firestore updated

---

### Test 4: Memory Retrieval
**Objective**: Verify Claude can recall stored facts

**Steps**:
1. Ask Claude to recall stored facts
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "saad@sakbark.com",
       "interface": "terminal",
       "message": "What do you know about me? List my favorite color, programming language, and workplace.",
       "stream": false
     }'
   ```
   Expected: Claude recalls: blue, TypeScript, Sakbark

2. Test from same conversation
   Expected: Maintains conversation context

3. Test from new conversation (different conversation_id)
   Expected: Still recalls facts (unified memory)

**Pass Criteria**: All facts recalled accurately across conversations

---

### Test 5: Cross-Interface Memory
**Objective**: Verify memory works across terminal and WhatsApp interfaces

**Steps**:
1. Store fact via terminal interface
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "saad@sakbark.com",
       "interface": "terminal",
       "message": "Remember: My birthday is January 15th",
       "stream": false
     }'
   ```

2. Recall via WhatsApp interface
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "saad@sakbark.com",
       "interface": "whatsapp",
       "message": "When is my birthday?",
       "stream": false
     }'
   ```
   Expected: Claude responds with "January 15th" and mentions it was told via terminal

3. Store via WhatsApp, recall via terminal
   Expected: Same unified memory behavior

**Pass Criteria**: Facts accessible from any interface, interface attribution present

---

### Test 6: WhatsApp Webhook Integration
**Objective**: Verify WhatsApp webhook forwards to Allspark correctly

**Steps**:
1. Test webhook test endpoint
   ```bash
   curl -X POST https://whatsapp-superclaud-958443682078.us-central1.run.app/test \
     -H "Content-Type: application/json" \
     -d '{
       "phone": "+1234567890",
       "message": "Test from webhook"
     }'
   ```
   Expected: Returns Claude response from Allspark

2. Check webhook logs for forwarding
   ```bash
   gcloud run services logs read whatsapp-superclaud \
     --region us-central1 --project new-fps-gpt --limit 10
   ```
   Expected: Shows forwarding to ALLSPARK_URL

3. Verify webhook has correct ALLSPARK_URL
   ```bash
   gcloud run services describe whatsapp-superclaud \
     --region us-central1 --project new-fps-gpt \
     --format='value(spec.template.spec.containers[0].env[?(@.name=="ALLSPARK_URL")].value)'
   ```
   Expected: Shows correct Allspark URL

**Pass Criteria**: Webhook forwards messages, receives responses, logs show proper flow

---

### Test 7: Streaming Responses
**Objective**: Verify streaming mode works correctly

**Steps**:
1. Test with stream=true
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "saad@sakbark.com",
       "interface": "terminal",
       "message": "Count to 5 slowly",
       "stream": true
     }'
   ```
   Expected: Server-sent events stream with incremental text

2. Test terminal client with streaming
   Expected: Real-time character-by-character display

**Pass Criteria**: Streaming works, events arrive progressively

---

### Test 8: Auto-Healing Mechanism
**Objective**: Verify monitoring and auto-repair works

**Steps**:
1. Run health monitor once
   ```bash
   /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service/health_monitor.sh once
   ```
   Expected: Reports healthy status

2. Check monitoring log
   ```bash
   cat /tmp/allspark_monitor.log
   ```
   Expected: Log entries present

3. Simulate failure scenario (scale to 0 temporarily)
   ```bash
   gcloud run services update allspark-claude \
     --min-instances 0 --region us-central1 --project new-fps-gpt
   sleep 10
   # Wait for cold start, then check health
   ```

4. Run monitor - should detect and repair
   ```bash
   /Users/saady/development/mcp-servers/memory-unified/cloud-claude-service/health_monitor.sh once
   ```
   Expected: Auto-scales back up, health restored

5. Restore min-instances
   ```bash
   gcloud run services update allspark-claude \
     --min-instances 1 --region us-central1 --project new-fps-gpt
   ```

**Pass Criteria**: Monitor detects issues, attempts repair, logs actions

---

### Test 9: Backup System
**Objective**: Verify backup script works correctly

**Steps**:
1. Run backup script
   ```bash
   /Users/saady/development/mcp-servers/memory-unified/backup_allspark.sh
   ```
   Expected: Creates backup directory, exports Firestore, commits to git

2. Verify backup directory created
   ```bash
   ls -la /Users/saady/allspark-backups/$(date +%Y-%m-%d)
   ```
   Expected: Contains manifest, YAML configs, logs

3. Check Firestore export initiated
   ```bash
   gcloud firestore operations list --project=new-fps-gpt
   ```
   Expected: Shows recent export operation

4. Verify git commit
   ```bash
   cd /Users/saady/development/mcp-servers/memory-unified
   git log -1
   ```
   Expected: Shows backup commit if changes exist

**Pass Criteria**: Backup completes, files created, Firestore exported, git updated

---

### Test 10: Auto-Upgrade System
**Objective**: Verify upgrade script can detect and apply updates

**Steps**:
1. Check current version
   ```bash
   cd /Users/saady/development/mcp-servers/memory-unified
   git rev-parse --short HEAD
   ```

2. Run upgrade check (when up to date)
   ```bash
   /Users/saady/development/mcp-servers/memory-unified/auto_upgrade.sh
   ```
   Expected: Reports "Already up to date"

3. (Manual test) Make a change, push, pull from another machine, run upgrade
   Expected: Detects update, shows changes, offers to upgrade

**Pass Criteria**: Detects updates correctly, can redeploy services

---

### Test 11: Conversation Management
**Objective**: Verify conversation CRUD operations

**Steps**:
1. List conversations
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/conversations
   ```
   Expected: Shows all active conversations

2. Create multiple conversations
   ```bash
   # Conversation 1
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -d '{"user_id":"saad@sakbark.com","conversation_id":"test1","message":"Test 1","stream":false}' \
     -H "Content-Type: application/json"

   # Conversation 2
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -d '{"user_id":"saad@sakbark.com","conversation_id":"test2","message":"Test 2","stream":false}' \
     -H "Content-Type: application/json"
   ```
   Expected: Two separate conversations

3. Delete conversation
   ```bash
   curl -X DELETE https://allspark-claude-958443682078.us-central1.run.app/conversations/saad@sakbark.com:test1
   ```
   Expected: Conversation deleted

4. Verify deletion
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/conversations
   ```
   Expected: test1 no longer listed

**Pass Criteria**: Can create, list, and delete conversations

---

### Test 12: Error Handling
**Objective**: Verify system handles errors gracefully

**Steps**:
1. Test with invalid user_id
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -d '{"interface":"terminal","message":"Test","stream":false}' \
     -H "Content-Type: application/json"
   ```
   Expected: Returns 400 error with clear message

2. Test with empty message
   ```bash
   curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -d '{"user_id":"test","interface":"terminal","message":"","stream":false}' \
     -H "Content-Type: application/json"
   ```
   Expected: Returns 400 error

3. Test webhook with malformed request
   ```bash
   curl -X POST https://whatsapp-superclaud-958443682078.us-central1.run.app/webhook/meta \
     -d '{"invalid":"data"}' \
     -H "Content-Type: application/json"
   ```
   Expected: Returns 200 with status "no_entry" (graceful handling)

4. Check error logs
   ```bash
   gcloud run services logs read allspark-claude \
     --region us-central1 --project new-fps-gpt \
     --format="value(textPayload)" | grep -i error
   ```
   Expected: Errors logged but not crashing

**Pass Criteria**: All errors handled gracefully, appropriate responses, no crashes

---

### Test 13: Performance and Scaling
**Objective**: Verify services scale and perform well

**Steps**:
1. Check current instance count
   ```bash
   gcloud run services describe allspark-claude \
     --region us-central1 --project new-fps-gpt \
     --format='value(status.traffic[0].latestRevision)'
   ```

2. Send multiple concurrent requests
   ```bash
   for i in {1..5}; do
     curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
       -d "{\"user_id\":\"user$i\",\"interface\":\"terminal\",\"message\":\"Test $i\",\"stream\":false}" \
       -H "Content-Type: application/json" &
   done
   wait
   ```
   Expected: All requests succeed

3. Check response times
   ```bash
   time curl -X POST https://allspark-claude-958443682078.us-central1.run.app/chat \
     -d '{"user_id":"saad@sakbark.com","interface":"terminal","message":"Quick test","stream":false}' \
     -H "Content-Type: application/json"
   ```
   Expected: Response within 10 seconds (warm instance)

**Pass Criteria**: Handles concurrent requests, reasonable response times

---

### Test 14: Security and Permissions
**Objective**: Verify proper security configuration

**Steps**:
1. Check service allows unauthenticated access (as intended)
   ```bash
   gcloud run services describe allspark-claude \
     --region us-central1 --project new-fps-gpt \
     --format='value(metadata.annotations."run.googleapis.com/ingress")'
   ```
   Expected: Shows "all"

2. Verify secrets are properly injected
   ```bash
   gcloud run services describe allspark-claude \
     --region us-central1 --project new-fps-gpt \
     --format='value(spec.template.spec.containers[0].env[?(@.name=="ANTHROPIC_API_KEY")].valueFrom.secretKeyRef.name)'
   ```
   Expected: Shows "anthropic-api-key"

3. Test that API key is not exposed
   ```bash
   curl https://allspark-claude-958443682078.us-central1.run.app/health
   ```
   Expected: No sensitive info in response

**Pass Criteria**: Proper access controls, secrets not exposed, auth configured

---

## Final Verification Checklist

After all tests complete:

- [ ] All services responding
- [ ] Terminal client working
- [ ] Memory storage confirmed
- [ ] Memory retrieval working
- [ ] Cross-interface memory verified
- [ ] WhatsApp webhook functional
- [ ] Streaming working
- [ ] Auto-healing tested
- [ ] Backup system operational
- [ ] Auto-upgrade functional
- [ ] Conversation management working
- [ ] Error handling graceful
- [ ] Performance acceptable
- [ ] Security configured properly

## Test Execution Log

### Execution Date: [FILL IN]
### Executed By: [FILL IN]
### Environment: Production / Staging / Local

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Service Health | ⏳ | |
| 2 | Terminal Client | ⏳ | |
| 3 | Memory Storage | ⏳ | |
| 4 | Memory Retrieval | ⏳ | |
| 5 | Cross-Interface | ⏳ | |
| 6 | WhatsApp Webhook | ⏳ | |
| 7 | Streaming | ⏳ | |
| 8 | Auto-Healing | ⏳ | |
| 9 | Backup System | ⏳ | |
| 10 | Auto-Upgrade | ⏳ | |
| 11 | Conversation Mgmt | ⏳ | |
| 12 | Error Handling | ⏳ | |
| 13 | Performance | ⏳ | |
| 14 | Security | ⏳ | |

Legend: ⏳ Pending | ✅ Pass | ❌ Fail | ⚠️ Partial
