#!/usr/bin/env python3
"""
Local Claude Service - The ONE True Entity

This service runs on your local machine and handles ALL Claude processing.
It has access to all MCP tools and acts as the unified consciousness.

The cloud Allspark routes ALL requests here, making this the single
source of truth for Claude's processing.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
import os
import json
import subprocess
import sys
from datetime import datetime
import hmac
from functools import wraps

app = Flask(__name__)
CORS(app)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# API key for authentication
API_KEY = os.environ.get('LOCAL_CLAUDE_API_KEY', 'dev-key-changeme')

# MCP client connections (we'll initialize these on startup)
mcp_clients = {}

def require_auth(f):
    """Require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization'}), 401

        token = auth_header[7:]
        if not hmac.compare_digest(token, API_KEY):
            return jsonify({'error': 'Invalid API key'}), 403

        return f(*args, **kwargs)
    return decorated

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'local-claude-service',
        'timestamp': datetime.utcnow().isoformat(),
        'mcp_servers': list(mcp_clients.keys())
    })

@app.route('/process', methods=['POST'])
@require_auth
def process():
    """
    Main processing endpoint
    This is where the Allspark routes all requests
    """
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    interface = data.get('interface', 'unknown')
    conversation_history = data.get('conversation_history', [])

    if not user_id or not message:
        return jsonify({'error': 'user_id and message required'}), 400

    # Build messages array for Claude
    messages = conversation_history.copy()
    messages.append({
        'role': 'user',
        'content': message
    })

    # System prompt with context
    system_prompt = f"""You are Claude, the unified AI assistant.

User: {user_id}
Interface: {interface}
Timestamp: {datetime.utcnow().isoformat()}

You have access to the unified memory system (Firestore) and all available MCP tools.
You are the ONE true Claude entity across all interfaces (terminal, WhatsApp, web, etc.).

Use your tools to help the user effectively. Remember that facts stored in memory
are available across all interfaces."""

    try:
        # Get available tools
        tools = get_tool_definitions()

        # Call Claude API with tools
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=system_prompt,
            tools=tools if tools else None,
            messages=messages
        )

        # Handle tool use if present
        assistant_message = ""
        tool_results = []

        for block in response.content:
            if block.type == 'text':
                assistant_message += block.text
            elif block.type == 'tool_use':
                # Execute tool
                tool_result = execute_tool(block.name, block.input)
                tool_results.append({
                    'tool_use_id': block.id,
                    'result': tool_result
                })

        # If we had tool use, make another API call with results
        if tool_results:
            messages.append({
                'role': 'assistant',
                'content': response.content
            })
            # Format tool results properly for Anthropic API
            tool_result_blocks = []
            for tr in tool_results:
                tool_result_blocks.append({
                    'type': 'tool_result',
                    'tool_use_id': tr['tool_use_id'],
                    'content': json.dumps(tr['result'])
                })
            messages.append({
                'role': 'user',
                'content': tool_result_blocks
            })

            # Second API call with tool results
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                system=system_prompt,
                messages=messages
            )

            assistant_message = ""
            for block in response.content:
                if block.type == 'text':
                    assistant_message += block.text

        return jsonify({
            'success': True,
            'response': assistant_message,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_tool_definitions():
    """
    Get tool definitions from available MCP servers
    For now, we'll return the memory tools we know exist
    """
    tools = [
        {
            "name": "get_unified_context",
            "description": "Get unified context from ALL interfaces (terminal, WhatsApp, etc). Returns recent messages and entities with interface attribution.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (email or phone)"
                    },
                    "max_messages": {
                        "type": "number",
                        "description": "Max messages to return (default: 20)",
                        "default": 20
                    }
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "create_unified_entities",
            "description": "Create entities in unified knowledge graph with interface tracking",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (email or phone)"
                    },
                    "interface": {
                        "type": "string",
                        "description": "Interface (terminal, whatsapp, etc)"
                    },
                    "entities": {
                        "type": "array",
                        "description": "Entities to create",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "entityType": {"type": "string"},
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["name", "entityType", "observations"]
                        }
                    }
                },
                "required": ["user_id", "interface", "entities"]
            }
        },
        {
            "name": "search_unified_memory",
            "description": "Search across ALL memory: entities, conversations, messages from all interfaces",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID (email or phone)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Max results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["user_id", "query"]
            }
        }
    ]

    return tools

def execute_tool(tool_name, parameters):
    """
    Execute a tool by calling the appropriate MCP server
    """
    try:
        # For now, we'll call the memory MCP server directly
        # This uses the index.js MCP server
        mcp_server_path = "/Users/saady/development/mcp-servers/memory-unified/index.js"

        # Build MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }

        # Call MCP server via node
        result = subprocess.run(
            ['node', mcp_server_path],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **os.environ,
                'GOOGLE_CLOUD_PROJECT': 'new-fps-gpt'
            }
        )

        if result.returncode != 0:
            return {
                'error': f'MCP server error: {result.stderr}',
                'success': False
            }

        # Parse response
        response = json.loads(result.stdout)
        return response.get('result', {})

    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print("=" * 60)
    print("  Local Claude Service - The Unified Entity")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Health: http://localhost:{port}/health")
    print(f"Process: POST http://localhost:{port}/process")
    print("=" * 60)
    print("This service handles ALL Claude processing across interfaces")
    print("The cloud Allspark routes requests here")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=False)
