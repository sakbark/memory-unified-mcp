#!/usr/bin/env node

import { Firestore } from '@google-cloud/firestore';

const db = new Firestore({
  projectId: 'new-fps-gpt',
});

async function checkMessages() {
  console.log('🔍 Checking for WhatsApp messages in Firestore...\n');

  try {
    const userRef = db.collection('users').doc('saad@sakbark.com');

    // Check context window
    const contextRef = userRef.collection('context_windows').doc('window_latest');
    const contextDoc = await contextRef.get();

    if (contextDoc.exists) {
      const data = contextDoc.data();
      console.log('✅ Context window exists!');
      console.log(`Messages count: ${(data.recent_messages || []).length}`);
      console.log('\nRecent messages:');
      (data.recent_messages || []).forEach((msg, i) => {
        console.log(`\n${i + 1}. [${msg.interface}] ${msg.role}:`);
        console.log(`   "${msg.content}"`);
        console.log(`   Time: ${msg.timestamp}`);
      });
    } else {
      console.log('❌ Context window does NOT exist');
    }

    console.log('\n---\n');

    // Check conversations
    const conversationsSnapshot = await userRef.collection('conversations').limit(5).get();
    console.log(`📝 Found ${conversationsSnapshot.size} conversations`);

    conversationsSnapshot.forEach(convDoc => {
      const conv = convDoc.data();
      console.log(`\nConversation: ${convDoc.id}`);
      console.log(`  Interfaces: ${(conv.interfaces_used || []).join(', ')}`);
      console.log(`  Updated: ${conv.metadata?.updated_at || 'unknown'}`);
    });

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

checkMessages();
