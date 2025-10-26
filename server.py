#!/usr/bin/env python3
"""
Memory MCP Server - Unified memory for Claude across all interfaces

Provides shared memory and knowledge graph that works across:
- Terminal (Claude Code)
- WhatsApp
- Any future interfaces

This creates ONE Claude entity, not multiple clones.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from google.cloud import firestore
from google.api_core import retry

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory-unified")

# Initialize Firestore
db = firestore.Client(project="new-fps-gpt")

# Server instance
app = Server("memory-unified")


# ============================================================================
# TOOLS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available memory tools"""
    return [
        Tool(
            name="create_entities",
            description="Create multiple new entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier (email or phone number)"
                    },
                    "interface": {
                        "type": "string",
                        "enum": ["terminal", "whatsapp"],
                        "description": "Which interface is creating these entities"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Current conversation ID"
                    },
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Entity name"
                                },
                                "entityType": {
                                    "type": "string",
                                    "description": "Type of entity (person, service, preference, etc.)"
                                },
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Observations about this entity"
                                }
                            },
                            "required": ["name", "entityType", "observations"]
                        }
                    }
                },
                "required": ["user_id", "interface", "entities"]
            }
        ),
        Tool(
            name="add_observations",
            description="Add new observations to existing entities in the knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "interface": {
                        "type": "string",
                        "enum": ["terminal", "whatsapp"],
                        "description": "Which interface is adding observations"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Current conversation ID"
                    },
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "entityName": {
                                    "type": "string",
                                    "description": "Name of the entity to add observations to"
                                },
                                "contents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "New observations to add"
                                }
                            },
                            "required": ["entityName", "contents"]
                        }
                    }
                },
                "required": ["user_id", "interface", "observations"]
            }
        ),
        Tool(
            name="search_memory",
            description="Search for information across conversations, entities, and context from ALL interfaces",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["entities", "conversations", "messages", "all"],
                        "default": "all",
                        "description": "What to search"
                    },
                    "interface_filter": {
                        "type": "string",
                        "enum": ["terminal", "whatsapp", "all"],
                        "default": "all",
                        "description": "Filter by interface"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum results to return"
                    }
                },
                "required": ["user_id", "query"]
            }
        ),
        Tool(
            name="get_unified_context",
            description="Get complete context for current conversation including messages and knowledge from ALL interfaces (terminal + WhatsApp)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "current_interface": {
                        "type": "string",
                        "enum": ["terminal", "whatsapp"],
                        "description": "Which interface is requesting context"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Current conversation ID (optional)"
                    },
                    "include_history": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include recent message history"
                    },
                    "max_messages": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum recent messages to include"
                    }
                },
                "required": ["user_id", "current_interface"]
            }
        ),
        Tool(
            name="sync_conversation_state",
            description="Save current conversation state so it's accessible from other interfaces",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "interface": {
                        "type": "string",
                        "enum": ["terminal", "whatsapp"],
                        "description": "Which interface is syncing"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Conversation ID"
                    },
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"},
                                "timestamp": {"type": "string"}
                            }
                        },
                        "description": "Messages to save"
                    },
                    "todos": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Active todos"
                    },
                    "context_summary": {
                        "type": "string",
                        "description": "Summary of current context"
                    }
                },
                "required": ["user_id", "interface", "conversation_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "create_entities":
            result = await create_entities(arguments)
        elif name == "add_observations":
            result = await add_observations(arguments)
        elif name == "search_memory":
            result = await search_memory(arguments)
        elif name == "get_unified_context":
            result = await get_unified_context(arguments)
        elif name == "sync_conversation_state":
            result = await sync_conversation_state(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def create_entities(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create new entities in the knowledge graph"""
    user_id = params["user_id"]
    interface = params["interface"]
    conversation_id = params.get("conversation_id")
    entities = params["entities"]

    created = []
    timestamp = datetime.utcnow()

    for entity in entities:
        entity_name = entity["name"]
        entity_type = entity["entityType"]
        observations = entity["observations"]

        # Create entity ID from name (sanitized)
        entity_id = f"entity_{entity_name.lower().replace(' ', '_').replace('-', '_')}"

        # Reference to entity document
        entity_ref = db.collection("users").document(user_id).collection("knowledge_graph").collection("entities").document(entity_id)

        # Check if entity exists
        entity_doc = entity_ref.get()

        if entity_doc.exists:
            # Entity exists, add observations to it
            existing_data = entity_doc.to_dict()
            existing_observations = existing_data.get("observations", [])

            # Add new observations
            for obs in observations:
                existing_observations.append({
                    "content": obs,
                    "learned_at": timestamp,
                    "learned_from_interface": interface,
                    "conversation_id": conversation_id
                })

            entity_ref.update({
                "observations": existing_observations,
                "updated_at": timestamp
            })

            created.append({
                "entity_id": entity_id,
                "name": entity_name,
                "status": "updated",
                "new_observations": len(observations)
            })
        else:
            # Create new entity
            observations_data = []
            for obs in observations:
                observations_data.append({
                    "content": obs,
                    "learned_at": timestamp,
                    "learned_from_interface": interface,
                    "conversation_id": conversation_id
                })

            entity_ref.set({
                "entity_id": entity_id,
                "name": entity_name,
                "entity_type": entity_type,
                "observations": observations_data,
                "relations": [],
                "metadata": {
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "confidence": 0.95
                }
            })

            created.append({
                "entity_id": entity_id,
                "name": entity_name,
                "status": "created",
                "observations_count": len(observations)
            })

    return {
        "success": True,
        "created_entities": created,
        "message": f"Created/updated {len(created)} entities in knowledge graph"
    }


async def add_observations(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add observations to existing entities"""
    user_id = params["user_id"]
    interface = params["interface"]
    conversation_id = params.get("conversation_id")
    observations = params["observations"]

    updated = []
    timestamp = datetime.utcnow()

    for obs_group in observations:
        entity_name = obs_group["entityName"]
        contents = obs_group["contents"]

        # Generate entity ID
        entity_id = f"entity_{entity_name.lower().replace(' ', '_').replace('-', '_')}"

        entity_ref = db.collection("users").document(user_id).collection("knowledge_graph").collection("entities").document(entity_id)

        entity_doc = entity_ref.get()

        if not entity_doc.exists:
            updated.append({
                "entity_name": entity_name,
                "status": "not_found",
                "message": f"Entity '{entity_name}' does not exist. Use create_entities first."
            })
            continue

        # Add observations
        existing_data = entity_doc.to_dict()
        existing_observations = existing_data.get("observations", [])

        for content in contents:
            existing_observations.append({
                "content": content,
                "learned_at": timestamp,
                "learned_from_interface": interface,
                "conversation_id": conversation_id
            })

        entity_ref.update({
            "observations": existing_observations,
            "updated_at": timestamp
        })

        updated.append({
            "entity_name": entity_name,
            "status": "updated",
            "new_observations": len(contents)
        })

    return {
        "success": True,
        "updated_entities": updated,
        "message": f"Added observations to {len([u for u in updated if u['status'] == 'updated'])} entities"
    }


async def search_memory(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search across all stored knowledge"""
    user_id = params["user_id"]
    query = params["query"].lower()
    search_type = params.get("search_type", "all")
    interface_filter = params.get("interface_filter", "all")
    max_results = params.get("max_results", 10)

    results = {
        "entities": [],
        "messages": [],
        "conversations": []
    }

    # Search entities
    if search_type in ["entities", "all"]:
        entities_ref = db.collection("users").document(user_id).collection("knowledge_graph").collection("entities")
        entities_docs = entities_ref.stream()

        for doc in entities_docs:
            entity = doc.to_dict()
            # Simple text search in name and observations
            if query in entity.get("name", "").lower() or any(query in obs.get("content", "").lower() for obs in entity.get("observations", [])):
                # Filter by interface if specified
                if interface_filter != "all":
                    # Only include observations from specified interface
                    filtered_obs = [obs for obs in entity.get("observations", []) if obs.get("learned_from_interface") == interface_filter]
                    if filtered_obs:
                        entity["observations"] = filtered_obs
                        results["entities"].append(entity)
                else:
                    results["entities"].append(entity)

            if len(results["entities"]) >= max_results:
                break

    # Search messages
    if search_type in ["messages", "all"]:
        # Get all conversations
        convs_ref = db.collection("users").document(user_id).collection("conversations")
        convs_docs = convs_ref.stream()

        for conv_doc in convs_docs:
            messages_ref = conv_doc.reference.collection("messages")
            messages_docs = messages_ref.stream()

            for msg_doc in messages_docs:
                msg = msg_doc.to_dict()
                if query in msg.get("content", "").lower():
                    # Filter by interface if specified
                    if interface_filter == "all" or msg.get("interface") == interface_filter:
                        results["messages"].append({
                            "conversation_id": conv_doc.id,
                            "message_id": msg_doc.id,
                            "role": msg.get("role"),
                            "content": msg.get("content"),
                            "interface": msg.get("interface"),
                            "timestamp": msg.get("timestamp")
                        })

                if len(results["messages"]) >= max_results:
                    break

            if len(results["messages"]) >= max_results:
                break

    return {
        "success": True,
        "query": query,
        "results": results,
        "total_entities": len(results["entities"]),
        "total_messages": len(results["messages"])
    }


async def get_unified_context(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get complete unified context from ALL interfaces"""
    user_id = params["user_id"]
    current_interface = params["current_interface"]
    conversation_id = params.get("conversation_id")
    include_history = params.get("include_history", True)
    max_messages = params.get("max_messages", 20)

    # Get user preferences
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        preferences = user_data.get("preferences", {})
        context_summary = user_data.get("context_summary", "")
        active_projects = user_data.get("active_projects", [])
    else:
        preferences = {}
        context_summary = ""
        active_projects = []

    # Get recent messages from context window
    recent_messages = []
    if include_history:
        context_ref = db.collection("users").document(user_id).collection("context_windows").document("window_latest")
        context_doc = context_ref.get()

        if context_doc.exists:
            context_data = context_doc.to_dict()
            recent_messages = context_data.get("recent_messages", [])[-max_messages:]

    # Get active todos from latest conversation
    active_todos = []
    if conversation_id:
        conv_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
        conv_doc = conv_ref.get()
        if conv_doc.exists:
            conv_data = conv_doc.to_dict()
            active_todos = conv_data.get("active_todos", [])

    # Get relevant entities (top recent ones)
    entities_ref = db.collection("users").document(user_id).collection("knowledge_graph").collection("entities")
    entities_docs = entities_ref.order_by("metadata.updated_at", direction=firestore.Query.DESCENDING).limit(10).stream()

    relevant_entities = []
    for doc in entities_docs:
        entity = doc.to_dict()
        relevant_entities.append({
            "name": entity.get("name"),
            "type": entity.get("entity_type"),
            "recent_observation": entity.get("observations", [])[-1] if entity.get("observations") else None
        })

    return {
        "success": True,
        "current_interface": current_interface,
        "context_summary": context_summary,
        "active_projects": active_projects,
        "active_todos": active_todos,
        "recent_messages": recent_messages,
        "user_preferences": preferences,
        "relevant_entities": relevant_entities,
        "message": f"Unified context retrieved - includes data from ALL interfaces (terminal + WhatsApp)"
    }


async def sync_conversation_state(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sync conversation state to make it accessible from other interfaces"""
    user_id = params["user_id"]
    interface = params["interface"]
    conversation_id = params["conversation_id"]
    messages = params.get("messages", [])
    todos = params.get("todos", [])
    context_summary = params.get("context_summary", "")

    timestamp = datetime.utcnow()

    # Update or create conversation document
    conv_ref = db.collection("users").document(user_id).collection("conversations").document(conversation_id)
    conv_doc = conv_ref.get()

    if conv_doc.exists:
        conv_data = conv_doc.to_dict()
        interfaces_used = conv_data.get("interfaces_used", [])
        if interface not in interfaces_used:
            interfaces_used.append(interface)

        conv_ref.update({
            "updated_at": timestamp,
            "interfaces_used": interfaces_used,
            "active_todos": todos,
            "context_summary": context_summary if context_summary else conv_data.get("context_summary", ""),
            "metadata.total_messages": firestore.Increment(len(messages))
        })
    else:
        conv_ref.set({
            "conversation_id": conversation_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "interfaces_used": [interface],
            "context_summary": context_summary,
            "active_todos": todos,
            "metadata": {
                "total_messages": len(messages),
                "tool_calls": 0
            }
        })

    # Save messages
    messages_saved = 0
    for msg in messages:
        msg_id = f"msg_{timestamp.timestamp()}_{messages_saved}"
        msg_ref = conv_ref.collection("messages").document(msg_id)

        msg_ref.set({
            "message_id": msg_id,
            "role": msg.get("role"),
            "content": msg.get("content"),
            "timestamp": msg.get("timestamp", timestamp),
            "interface": interface
        })
        messages_saved += 1

    # Update context window
    context_ref = db.collection("users").document(user_id).collection("context_windows").document("window_latest")
    context_doc = context_ref.get()

    if context_doc.exists:
        context_data = context_doc.to_dict()
        recent_messages = context_data.get("recent_messages", [])

        # Add new messages
        for msg in messages:
            recent_messages.append({
                "role": msg.get("role"),
                "content": msg.get("content"),
                "interface": interface,
                "timestamp": msg.get("timestamp", timestamp).isoformat() if isinstance(msg.get("timestamp"), datetime) else str(msg.get("timestamp", timestamp))
            })

        # Keep only last 50 messages
        recent_messages = recent_messages[-50:]

        context_ref.update({
            "updated_at": timestamp,
            "summary": context_summary if context_summary else context_data.get("summary", ""),
            "active_tasks": [todo.get("content") for todo in todos] if todos else context_data.get("active_tasks", []),
            "recent_messages": recent_messages
        })
    else:
        # Create new context window
        context_ref.set({
            "window_id": "window_latest",
            "created_at": timestamp,
            "updated_at": timestamp,
            "expires_at": timestamp + timedelta(days=7),
            "summary": context_summary,
            "active_tasks": [todo.get("content") for todo in todos] if todos else [],
            "recent_messages": [
                {
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "interface": interface,
                    "timestamp": msg.get("timestamp", timestamp).isoformat() if isinstance(msg.get("timestamp"), datetime) else str(msg.get("timestamp", timestamp))
                }
                for msg in messages
            ]
        })

    # Update user's last interaction
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        "user_id": user_id,
        "last_interaction": {
            "interface": interface,
            "timestamp": timestamp
        },
        "context_summary": context_summary if context_summary else firestore.firestore.SERVER_TIMESTAMP
    }, merge=True)

    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages_saved": messages_saved,
        "interface": interface,
        "message": f"Conversation state synced - now accessible from ALL interfaces"
    }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the server"""
    logger.info("Starting Memory Unified MCP Server")
    logger.info("This server creates ONE Claude entity across all interfaces")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
