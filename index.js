#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { Firestore } from '@google-cloud/firestore';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const keyPath = join(__dirname, 'service-account-key.json');

const dbConfig = {
  projectId: 'new-fps-gpt',
};

// Use service account key if it exists (for local development)
if (existsSync(keyPath)) {
  dbConfig.keyFilename = keyPath;
}

const db = new Firestore(dbConfig);

// Helper function to resolve user ID (email or phone) to primary ID
async function resolveUserId(inputId) {
  // Check if there's a mapping for this ID
  const mappingDoc = await db.collection('user_mappings').doc(inputId).get();

  if (mappingDoc.exists) {
    const mappingData = mappingDoc.data();
    return mappingData.primary_id;
  }

  // If no mapping exists, return the input ID as-is
  return inputId;
}

const server = new Server(
  {
    name: 'memory-unified',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool 1: get_unified_context - Get context from ALL interfaces
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'get_unified_context',
        description: 'Get unified context from ALL interfaces (terminal, WhatsApp, etc). Returns recent messages and entities with interface attribution.',
        inputSchema: {
          type: 'object',
          properties: {
            user_id: {
              type: 'string',
              description: 'User ID (email or phone)',
            },
            max_messages: {
              type: 'number',
              description: 'Max messages to return (default: 20)',
              default: 20,
            },
          },
          required: ['user_id'],
        },
      },
      {
        name: 'search_unified_memory',
        description: 'Search across ALL memory: entities, conversations, messages from all interfaces',
        inputSchema: {
          type: 'object',
          properties: {
            user_id: {
              type: 'string',
              description: 'User ID (email or phone)',
            },
            query: {
              type: 'string',
              description: 'Search query',
            },
            max_results: {
              type: 'number',
              description: 'Max results (default: 10)',
              default: 10,
            },
          },
          required: ['user_id', 'query'],
        },
      },
      {
        name: 'create_unified_entities',
        description: 'Create entities in unified knowledge graph with interface tracking',
        inputSchema: {
          type: 'object',
          properties: {
            user_id: {
              type: 'string',
              description: 'User ID (email or phone)',
            },
            interface: {
              type: 'string',
              description: 'Interface (terminal, whatsapp, etc)',
            },
            entities: {
              type: 'array',
              description: 'Entities to create',
              items: {
                type: 'object',
                properties: {
                  name: { type: 'string' },
                  entityType: { type: 'string' },
                  observations: {
                    type: 'array',
                    items: { type: 'string' },
                  },
                },
                required: ['name', 'entityType', 'observations'],
              },
            },
          },
          required: ['user_id', 'interface', 'entities'],
        },
      },
      {
        name: 'sync_conversation_state',
        description: 'Sync conversation state across interfaces',
        inputSchema: {
          type: 'object',
          properties: {
            user_id: {
              type: 'string',
              description: 'User ID (email or phone)',
            },
            interface: {
              type: 'string',
              description: 'Source interface',
            },
            messages: {
              type: 'array',
              description: 'Messages to sync',
              items: {
                type: 'object',
                properties: {
                  role: { type: 'string' },
                  content: { type: 'string' },
                  timestamp: { type: 'string' },
                },
                required: ['role', 'content'],
              },
            },
          },
          required: ['user_id', 'interface', 'messages'],
        },
      },
    ],
  };
});

// Tool handlers
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'get_unified_context': {
        const { user_id, max_messages = 20 } = args;
        const resolvedUserId = await resolveUserId(user_id);
        const userRef = db.collection('users').doc(resolvedUserId);

        // Get context window
        const contextDoc = await userRef.collection('context_windows').doc('window_latest').get();
        const contextData = contextDoc.exists ? contextDoc.data() : {};

        // Get recent entities
        const entitiesSnapshot = await userRef
          .collection('entities')
          .orderBy('metadata.updated_at', 'desc')
          .limit(10)
          .get();

        const entities = [];
        entitiesSnapshot.forEach(doc => {
          const data = doc.data();
          entities.push({
            name: data.name,
            type: data.entity_type,
            observations: data.observations || [],
          });
        });

        const result = {
          user_id,
          context_summary: contextData.summary || 'No summary',
          recent_messages: (contextData.recent_messages || []).slice(0, max_messages),
          entities,
          message_count: (contextData.recent_messages || []).length,
        };

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'search_unified_memory': {
        const { user_id, query, max_results = 10 } = args;
        const resolvedUserId = await resolveUserId(user_id);
        const userRef = db.collection('users').doc(resolvedUserId);
        const queryLower = query.toLowerCase();

        const results = {
          messages: [],
          entities: [],
        };

        // Search messages in context window
        const contextDoc = await userRef.collection('context_windows').doc('window_latest').get();
        if (contextDoc.exists) {
          const messages = contextDoc.data().recent_messages || [];
          results.messages = messages
            .filter(msg => msg.content.toLowerCase().includes(queryLower))
            .slice(0, max_results);
        }

        // Search entities
        const entitiesSnapshot = await userRef.collection('entities').get();
        entitiesSnapshot.forEach(doc => {
          const data = doc.data();
          const nameMatch = data.name.toLowerCase().includes(queryLower);
          const obsMatch = (data.observations || []).some(obs =>
            obs.content?.toLowerCase().includes(queryLower)
          );

          if (nameMatch || obsMatch) {
            results.entities.push({
              name: data.name,
              type: data.entity_type,
              observations: data.observations || [],
            });
          }
        });

        results.entities = results.entities.slice(0, max_results);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }

      case 'create_unified_entities': {
        const { user_id, interface: sourceInterface, entities } = args;
        const resolvedUserId = await resolveUserId(user_id);
        const userRef = db.collection('users').doc(resolvedUserId);
        const created = [];

        for (const entity of entities) {
          const entityId = `entity_${entity.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
          const entityRef = userRef.collection('entities').doc(entityId);

          const observations = entity.observations.map(obs => ({
            content: obs,
            learned_at: new Date().toISOString(),
            learned_from_interface: sourceInterface,
          }));

          await entityRef.set({
            entity_id: entityId,
            name: entity.name,
            entity_type: entity.entityType,
            observations,
            metadata: {
              created_at: Firestore.FieldValue.serverTimestamp(),
              updated_at: Firestore.FieldValue.serverTimestamp(),
            },
          });

          created.push({
            entity_id: entityId,
            name: entity.name,
            interface: sourceInterface,
          });
        }

        return {
          content: [
            {
              type: 'text',
              text: `Created ${created.length} entities from ${sourceInterface}: ${JSON.stringify(created, null, 2)}`,
            },
          ],
        };
      }

      case 'sync_conversation_state': {
        const { user_id, interface: sourceInterface, messages } = args;
        const resolvedUserId = await resolveUserId(user_id);
        const userRef = db.collection('users').doc(resolvedUserId);
        const contextRef = userRef.collection('context_windows').doc('window_latest');

        const formattedMessages = messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          interface: sourceInterface,
          timestamp: msg.timestamp || new Date().toISOString(),
        }));

        await contextRef.set(
          {
            recent_messages: Firestore.FieldValue.arrayUnion(...formattedMessages),
            updated_at: Firestore.FieldValue.serverTimestamp(),
          },
          { merge: true }
        );

        return {
          content: [
            {
              type: 'text',
              text: `Synced ${messages.length} messages from ${sourceInterface}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Unified Memory MCP Server running on stdio');
}

main().catch(console.error);
