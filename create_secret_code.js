import { Firestore } from '@google-cloud/firestore';

const db = new Firestore({
  projectId: 'new-fps-gpt',
  keyFilename: './service-account-key.json'
});

async function createSecretCode() {
  const userId = '+447933993951'; // Your primary ID
  const userRef = db.collection('users').doc(userId);
  const contextRef = userRef.collection('context_windows').doc('window_latest');

  // Create secret test entity
  const entityRef = userRef.collection('entities').doc('entity_secret_code_allspark_test');

  await entityRef.set({
    entity_id: 'entity_secret_code_allspark_test',
    name: 'Allspark Secret Code',
    entity_type: 'verification_test',
    observations: [
      {
        content: '🔐 SECRET CODE: MEXICAN-CHICKEN-42',
        learned_at: new Date().toISOString(),
        learned_from_interface: 'terminal_setup'
      },
      {
        content: 'This secret code proves The Allspark unified memory is operational',
        learned_at: new Date().toISOString(),
        learned_from_interface: 'terminal_setup'
      },
      {
        content: 'Created during Mexican food outing on 2025-10-26',
        learned_at: new Date().toISOString(),
        learned_from_interface: 'terminal_setup'
      }
    ],
    metadata: {
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  });

  // Also add a secret message to context
  await contextRef.set(
    {
      recent_messages: Firestore.FieldValue.arrayUnion({
        role: 'system',
        content: '🔐 VERIFICATION TEST: Secret code is MEXICAN-CHICKEN-42. Ask Claude for "the secret code" to verify unified memory.',
        interface: 'terminal_setup',
        timestamp: new Date().toISOString()
      }),
      updated_at: new Date().toISOString()
    },
    { merge: true }
  );

  console.log('✅ Secret code created!');
  console.log('🔐 SECRET CODE: MEXICAN-CHICKEN-42');
  console.log('\nTo verify after restart, ask Claude:');
  console.log('  "What is the secret code?"');
  console.log('  "Show me the Allspark secret code"');
  console.log('  "Search my memory for secret code"');
  console.log('\nIf Claude can retrieve it, The Allspark is working! 🚀');
}

createSecretCode().catch(console.error);
