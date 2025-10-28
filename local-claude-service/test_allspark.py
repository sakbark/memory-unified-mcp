#!/usr/bin/env python3
import requests
import json

response = requests.post(
    'https://allspark-claude-958443682078.us-central1.run.app/chat',
    headers={'Content-Type': 'application/json'},
    json={
        'user_id': 'saad@sakbark.com',
        'message': 'Reply with YES',
        'interface': 'test'
    },
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
