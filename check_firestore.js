#!/usr/bin/env node

import { Firestore } from '@google-cloud/firestore';

const db = new Firestore({
  projectId: 'new-fps-gpt',
});

async function checkFirestore() {
  console.log('🔍 Checking Firestore data...\n');

  try {
    // Check if user document exists
    const userRef = db.collection('users').doc('saad@sakbark.com');
    const userDoc = await userRef.get();

    if (userDoc.exists) {
      console.log('✅ User document exists');
      console.log('Data:', JSON.stringify(userDoc.data(), null, 2));
    } else {
      console.log('❌ User document does NOT exist');
    }

    console.log('\n---\n');

    // Check entities
    const entitiesSnapshot = await userRef
      .collection('knowledge_graph')
      .collection('entities')
      .limit(5)
      .get();

    console.log(`📦 Found ${entitiesSnapshot.size} entities`);
    entitiesSnapshot.forEach(doc => {
      const data = doc.data();
      console.log(`  - ${data.name} (${data.entity_type})`);
      if (data.observations && data.observations.length > 0) {
        console.log(`    Last observation: "${data.observations[data.observations.length - 1].content}"`);
        console.log(`    Learned via: ${data.observations[data.observations.length - 1].learned_from_interface}`);
      }
    });

    console.log('\n---\n');

    // Check context window
    const contextRef = userRef.collection('context_windows').doc('window_latest');
    const contextDoc = await contextRef.get();

    if (contextDoc.exists) {
      const contextData = contextDoc.data();
      console.log('✅ Context window exists');
      console.log(`   Messages: ${(contextData.recent_messages || []).length}`);
      console.log(`   Summary: ${contextData.summary || 'None'}`);
    } else {
      console.log('❌ Context window does NOT exist');
    }

    console.log('\n✅ Firestore connectivity confirmed');

  } catch (error) {
    console.error('❌ Firestore error:', error.message);
    process.exit(1);
  }
}

checkFirestore();
