#!/usr/bin/env python3
"""
Allspark Cloud Claude Service
A persistent Claude instance running in the cloud with unified memory
Handles requests from multiple interfaces (terminal, WhatsApp, etc.)
"""

from flask import Flask, request, jsonify, Response
from anthropic import Anthropic
import os
import sys
import json
from datetime import datetime
import asyncio
from functools import wraps

# Add parent directory to path for MCP server imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Store active conversations
conversations = {}

def stream_sse(generator):
    """Convert generator to Server-Sent Events format"""
    def generate():
        for data in generator:
            if data:
                yield f"data: {json.dumps(data)}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'allspark-claude',
        'timestamp': datetime.utcnow().isoformat(),
        'active_conversations': len(conversations)
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Accepts: {
        "user_id": "saad@sakbark.com",
        "interface": "terminal",
        "message": "What's the weather?",
        "conversation_id": "optional-conversation-id",
        "stream": true/false
    }
    """
    data = request.json
    user_id = data.get('user_id')
    interface = data.get('interface', 'terminal')
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    stream = data.get('stream', True)

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

    # Add user message
    conversation['messages'].append({
        'role': 'user',
        'content': message
    })

    # Build system prompt with unified memory context
    system_prompt = f"""You are Claude, running in The Allspark - a unified memory system.

User ID: {user_id}
Current Interface: {interface}
Conversation ID: {conversation_id or 'default'}

You have access to unified memory across all interfaces (terminal, WhatsApp, etc.).
Use the memory MCP tools to:
- Remember facts about the user
- Retrieve context from previous conversations
- Sync state across interfaces

The user can interact with you from multiple interfaces, and you should maintain context across all of them."""

    # Make API call to Claude
    if stream:
        def generate_stream():
            try:
                with anthropic_client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=conversation['messages']
                ) as stream:
                    full_response = ""
                    for text in stream.text_stream:
                        full_response += text
                        yield {'type': 'text', 'content': text}

                    # Add assistant response to conversation
                    conversation['messages'].append({
                        'role': 'assistant',
                        'content': full_response
                    })
                    yield {'type': 'done', 'full_response': full_response}
            except Exception as e:
                yield {'type': 'error', 'error': str(e)}

        return stream_sse(generate_stream())
    else:
        try:
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=conversation['messages']
            )

            assistant_message = response.content[0].text

            # Add to conversation
            conversation['messages'].append({
                'role': 'assistant',
                'content': assistant_message
            })

            return jsonify({
                'response': assistant_message,
                'conversation_id': conversation_id or 'default',
                'message_count': len(conversation['messages'])
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

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

@app.route('/conversations/<conversation_key>', methods=['DELETE'])
def delete_conversation(conversation_key):
    """Delete a conversation"""
    if conversation_key in conversations:
        del conversations[conversation_key]
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'conversation not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"⚡ Allspark Cloud Claude Service starting on port {port}")
    print(f"🧠 Unified memory enabled")
    print(f"🌐 Ready to serve multiple interfaces")
    app.run(host='0.0.0.0', port=port, debug=False)
