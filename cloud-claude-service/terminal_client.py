#!/usr/bin/env python3
"""
Allspark Terminal Client
Connects to the cloud-hosted Claude instance
Provides a rich terminal interface for interacting with The Allspark
"""

import requests
import sys
import os
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
import sseclient

console = Console()

# Default cloud service URL (can be overridden with env var)
SERVICE_URL = os.environ.get('ALLSPARK_URL', 'http://localhost:8080')
USER_ID = os.environ.get('USER_EMAIL', 'saad@sakbark.com')

def check_service_health():
    """Check if the cloud service is running"""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            console.print(f"[green]✓[/green] Connected to Allspark")
            console.print(f"[dim]  Active conversations: {health['active_conversations']}[/dim]")
            return True
    except requests.exceptions.RequestException:
        console.print(f"[red]✗[/red] Cannot connect to Allspark at {SERVICE_URL}")
        console.print(f"[yellow]Tip:[/yellow] Make sure the service is running:")
        console.print(f"[dim]  python3 cloud-claude-service/server.py[/dim]")
        return False

def send_message_stream(message, conversation_id=None):
    """Send a message and stream the response"""
    try:
        response = requests.post(
            f"{SERVICE_URL}/chat",
            json={
                'user_id': USER_ID,
                'interface': 'terminal',
                'message': message,
                'conversation_id': conversation_id,
                'stream': True
            },
            stream=True,
            timeout=120
        )

        if response.status_code != 200:
            console.print(f"[red]Error:[/red] {response.text}")
            return

        # Stream the response
        console.print()
        full_response = ""

        client = sseclient.SSEClient(response)
        for event in client.events():
            data = json.loads(event.data)

            if data['type'] == 'text':
                full_response += data['content']
                console.print(data['content'], end='')
            elif data['type'] == 'done':
                console.print()
                break
            elif data['type'] == 'error':
                console.print(f"\n[red]Error:[/red] {data['error']}")
                break

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")

def main():
    """Main terminal interface"""
    console.print()
    console.print(Panel.fit(
        "[bold blue]⚡ The Allspark[/bold blue]\n"
        "[dim]Unified Claude Consciousness[/dim]\n\n"
        f"[green]Connected as:[/green] {USER_ID}\n"
        f"[green]Interface:[/green] Terminal",
        border_style="blue"
    ))
    console.print()

    # Check service health
    if not check_service_health():
        sys.exit(1)

    console.print()
    console.print("[dim]Type 'exit' or 'quit' to end session[/dim]")
    console.print("[dim]Press Ctrl+C to interrupt a response[/dim]")
    console.print()

    conversation_id = None

    while True:
        try:
            # Get user input
            message = Prompt.ask("[bold cyan]You[/bold cyan]")

            if message.lower() in ['exit', 'quit', 'bye']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not message.strip():
                continue

            # Send message and stream response
            console.print("[bold magenta]Claude[/bold magenta]:", end=' ')
            send_message_stream(message, conversation_id)
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")

if __name__ == '__main__':
    main()
