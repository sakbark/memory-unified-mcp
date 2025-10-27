#!/usr/bin/env python3
"""
Allspark Cloud Claude Service - Unified Entity Version

This service acts as a routing + memory layer.
ALL processing is handled by the local Claude Code instance.

This makes the system a TRUE unified entity - not a copy, but the same Claude.
"""

from flask import Flask, request, jsonify, Response
import os
import json
from datetime import datetime
import requests
from google.cloud import firestore

app = Flask(__name__)

# Initialize Firestore
db = firestore.Client(project=os.environ.get('GOOGLE_CLOUD_PROJECT', 'new-fps-gpt'))

# Local Claude service URL (from Secret Manager or env)
LOCAL_CLAUDE_URL = os.environ.get('LOCAL_CLAUDE_URL', '')
LOCAL_CLAUDE_API_KEY = os.environ.get('LOCAL_CLAUDE_API_KEY', '')

# Fallback Anthropic client (if local unavailable)
from anthropic import Anthropic
anthropic_fallback = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Store active conversations
conversations = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if local Claude is available
    local_status = 'unknown'
    try:
        if LOCAL_CLAUDE_URL:
            response = requests.get(f"{LOCAL_CLAUDE_URL}/health", timeout=3)
            local_status = 'connected' if response.status_code == 200 else 'error'
        else:
            local_status = 'not_configured'
    except:
        local_status = 'unreachable'

    return jsonify({
        'status': 'healthy',
        'service': 'allspark-claude-unified',
        'timestamp': datetime.utcnow().isoformat(),
        'active_conversations': len(conversations),
        'local_claude_status': local_status,
        'mode': 'unified' if local_status == 'connected' else 'fallback'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Routes requests to local Claude Code instance
    """
    data = request.json
    user_id = data.get('user_id')
    interface = data.get('interface', 'terminal')
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    stream = data.get('stream', False)

    if not user_id or not message:
        return jsonify({'error': 'user_id and message are required'}), 400

    # Get or create conversation
    conv_key = f"{user_id}:{conversation_id}" if conversation_id else f"{user_id}:default"
    if conv_key not in conversations:
        conversations[conv_key] = {
            'messages': [],
            'user_id': user_id,
            'interface': interface,
            'created_at': datetime.utcnow().isoformat()
        }

    conversation = conversations[conv_key]

    # Store message in Firestore
    store_message_firestore(user_id, interface, message, 'user')

    # Add user message to conversation
    conversation['messages'].append({
        'role': 'user',
        'content': message
    })

    # Try to route to local Claude
    if LOCAL_CLAUDE_URL and LOCAL_CLAUDE_API_KEY:
        try:
            response = requests.post(
                f"{LOCAL_CLAUDE_URL}/process",
                json={
                    'user_id': user_id,
                    'interface': interface,
                    'message': message,
                    'conversation_history': conversation['messages'][:-1]  # Don't include the message we just added
                },
                headers={
                    'Authorization': f'Bearer {LOCAL_CLAUDE_API_KEY}',
                    'Content-Type': 'application/json'
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('response', '')

                # Add to conversation
                conversation['messages'].append({
                    'role': 'assistant',
                    'content': assistant_message
                })

                # Store in Firestore
                store_message_firestore(user_id, interface, assistant_message, 'assistant')

                return jsonify({
                    'response': assistant_message,
                    'conversation_id': conversation_id or 'default',
                    'message_count': len(conversation['messages']),
                    'mode': 'unified_entity',
                    'processed_by': 'local_claude_code'
                })

        except Exception as e:
            print(f"Error routing to local Claude: {e}")
            # Fall through to fallback

    # Fallback: Use cloud Claude directly (not unified, but better than nothing)
    try:
        response = anthropic_fallback.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=f"""You are Claude, running in The Allspark.
WARNING: You are in FALLBACK mode - the unified entity connection is unavailable.

User: {user_id}
Interface: {interface}

You have limited capabilities in this mode.""",
            messages=conversation['messages']
        )

        assistant_message = response.content[0].text

        # Add to conversation
        conversation['messages'].append({
            'role': 'assistant',
            'content': assistant_message
        })

        # Store in Firestore
        store_message_firestore(user_id, interface, assistant_message, 'assistant')

        return jsonify({
            'response': assistant_message,
            'conversation_id': conversation_id or 'default',
            'message_count': len(conversation['messages']),
            'mode': 'fallback',
            'warning': 'Unified entity connection unavailable - using fallback mode'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def store_message_firestore(user_id, interface, content, role):
    """Store message in Firestore unified memory"""
    try:
        doc_ref = db.collection('conversations').document(user_id).collection('messages').document()
        doc_ref.set({
            'user_id': user_id,
            'interface': interface,
            'content': content,
            'role': role,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    except Exception as e:
        print(f"Error storing message: {e}")

@app.route('/conversations', methods=['GET'])
def list_conversations():
    """List all active conversations"""
    return jsonify({
        'conversations': [
            {
                'key': key,
                'user_id': conv['user_id'],
                'interface': conv['interface'],
                'message_count': len(conv['messages']),
                'created_at': conv['created_at']
            }
            for key, conv in conversations.items()
        ]
    })

@app.route('/conversations/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    """Delete a conversation"""
    if conv_id in conversations:
        del conversations[conv_id]
        return jsonify({'success': True})
    return jsonify({'error': 'Conversation not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 70)
    print("  Allspark Cloud Service - Unified Entity Mode")
    print("=" * 70)
    print(f"Port: {port}")
    print(f"Local Claude URL: {LOCAL_CLAUDE_URL or 'NOT CONFIGURED'}")
    print(f"Mode: {'UNIFIED ENTITY' if LOCAL_CLAUDE_URL else 'FALLBACK ONLY'}")
    print("=" * 70)
    print("This service routes ALL requests to the local Claude Code instance")
    print("Making the system a TRUE unified entity across all interfaces")
    print("=" * 70)

    app.run(host='0.0.0.0', port=port, debug=False)
