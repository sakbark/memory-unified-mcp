#!/usr/bin/env python3
"""
MCP Bridge Proxy

Exposes local tool execution capabilities to the cloud Allspark instance.
Provides a REST API that the cloud can call to execute tools locally.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import json
import hashlib
import hmac
from functools import wraps
from datetime import datetime

app = Flask(__name__)
CORS(app)

# API key for authentication (from environment or Secret Manager)
API_KEY = os.environ.get('BRIDGE_API_KEY', 'dev-key-changeme')

def require_auth(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        if not hmac.compare_digest(token, API_KEY):
            return jsonify({'error': 'Invalid API key'}), 403

        return f(*args, **kwargs)
    return decorated

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'mcp-bridge-proxy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/list-tools', methods=['GET'])
@require_auth
def list_tools():
    """List all available tools"""
    tools = [
        # Filesystem tools
        {
            'name': 'read_file',
            'description': 'Read contents of a file',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Absolute file path'}
                },
                'required': ['path']
            }
        },
        {
            'name': 'write_file',
            'description': 'Write content to a file',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Absolute file path'},
                    'content': {'type': 'string', 'description': 'File content'}
                },
                'required': ['path', 'content']
            }
        },
        {
            'name': 'list_directory',
            'description': 'List files in a directory',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Directory path'}
                },
                'required': ['path']
            }
        },
        {
            'name': 'execute_command',
            'description': 'Execute a shell command',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string', 'description': 'Shell command to execute'},
                    'timeout': {'type': 'number', 'description': 'Timeout in seconds', 'default': 30}
                },
                'required': ['command']
            }
        },
        # Git tools
        {
            'name': 'git_status',
            'description': 'Get git repository status',
            'parameters': {
                'type': 'object',
                'properties': {
                    'repo_path': {'type': 'string', 'description': 'Repository path'}
                },
                'required': ['repo_path']
            }
        },
        {
            'name': 'git_commit',
            'description': 'Commit changes to git',
            'parameters': {
                'type': 'object',
                'properties': {
                    'repo_path': {'type': 'string', 'description': 'Repository path'},
                    'message': {'type': 'string', 'description': 'Commit message'},
                    'files': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Files to commit (or all if empty)'}
                },
                'required': ['repo_path', 'message']
            }
        }
    ]

    return jsonify({'tools': tools})

@app.route('/execute-tool', methods=['POST'])
@require_auth
def execute_tool():
    """Execute a tool and return the result"""
    data = request.json
    tool_name = data.get('tool_name')
    parameters = data.get('parameters', {})

    if not tool_name:
        return jsonify({'error': 'tool_name is required'}), 400

    try:
        # Route to appropriate tool handler
        if tool_name == 'read_file':
            result = tool_read_file(parameters)
        elif tool_name == 'write_file':
            result = tool_write_file(parameters)
        elif tool_name == 'list_directory':
            result = tool_list_directory(parameters)
        elif tool_name == 'execute_command':
            result = tool_execute_command(parameters)
        elif tool_name == 'git_status':
            result = tool_git_status(parameters)
        elif tool_name == 'git_commit':
            result = tool_git_commit(parameters)
        else:
            return jsonify({'error': f'Unknown tool: {tool_name}'}), 400

        return jsonify({
            'success': True,
            'tool_name': tool_name,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'tool_name': tool_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Tool implementations

def tool_read_file(params):
    """Read file contents"""
    path = params['path']
    if not os.path.isabs(path):
        raise ValueError('Path must be absolute')

    with open(path, 'r') as f:
        content = f.read()

    return {
        'path': path,
        'content': content,
        'size': len(content),
        'lines': len(content.split('\n'))
    }

def tool_write_file(params):
    """Write content to file"""
    path = params['path']
    content = params['content']

    if not os.path.isabs(path):
        raise ValueError('Path must be absolute')

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'w') as f:
        f.write(content)

    return {
        'path': path,
        'bytes_written': len(content),
        'success': True
    }

def tool_list_directory(params):
    """List directory contents"""
    path = params['path']

    if not os.path.exists(path):
        raise ValueError(f'Directory does not exist: {path}')

    if not os.path.isdir(path):
        raise ValueError(f'Path is not a directory: {path}')

    entries = []
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        stat = os.stat(full_path)
        entries.append({
            'name': entry,
            'type': 'directory' if os.path.isdir(full_path) else 'file',
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return {
        'path': path,
        'entries': entries,
        'count': len(entries)
    }

def tool_execute_command(params):
    """Execute shell command"""
    command = params['command']
    timeout = params.get('timeout', 30)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            'command': command,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'success': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        raise ValueError(f'Command timed out after {timeout} seconds')

def tool_git_status(params):
    """Get git repository status"""
    repo_path = params['repo_path']

    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise ValueError(f'Git command failed: {result.stderr}')

    return {
        'repo_path': repo_path,
        'status': result.stdout,
        'has_changes': bool(result.stdout.strip())
    }

def tool_git_commit(params):
    """Commit changes to git"""
    repo_path = params['repo_path']
    message = params['message']
    files = params.get('files', [])

    # Add files
    if files:
        for file in files:
            subprocess.run(
                ['git', 'add', file],
                cwd=repo_path,
                check=True
            )
    else:
        subprocess.run(
            ['git', 'add', '-A'],
            cwd=repo_path,
            check=True
        )

    # Commit
    result = subprocess.run(
        ['git', 'commit', '-m', message],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    return {
        'repo_path': repo_path,
        'message': message,
        'output': result.stdout,
        'success': result.returncode == 0
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting MCP Bridge Proxy on port {port}...")
    print(f"Health check: http://localhost:{port}/health")
    print(f"API Key required for authenticated endpoints")
    app.run(host='0.0.0.0', port=port, debug=False)
