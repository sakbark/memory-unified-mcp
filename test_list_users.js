import { Firestore } from '@google-cloud/firestore';

const db = new Firestore({
  projectId: 'new-fps-gpt',
  keyFilename: './service-account-key.json'
});

async function listUsers() {
  const usersSnapshot = await db.collection('users').limit(10).get();
  console.log(`\nFound ${usersSnapshot.size} users:`);
  usersSnapshot.forEach(doc => {
    console.log(`  - ${doc.id}`);
  });
}

listUsers().catch(console.error);
