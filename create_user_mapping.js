import { Firestore } from '@google-cloud/firestore';

const db = new Firestore({
  projectId: 'new-fps-gpt',
  keyFilename: './service-account-key.json'
});

async function createUserMapping() {
  // Create mapping: email -> phone
  await db.collection('user_mappings').doc('saad@sakbark.com').set({
    primary_id: '+447933993951',
    email: 'saad@sakbark.com',
    phone: '+447933993951',
    created_at: new Date().toISOString()
  });
  
  // Create reverse mapping: phone -> email  
  await db.collection('user_mappings').doc('+447933993951').set({
    primary_id: '+447933993951',
    email: 'saad@sakbark.com',
    phone: '+447933993951',
    created_at: new Date().toISOString()
  });
  
  console.log('✅ User mapping created: saad@sakbark.com <-> +447933993951');
}

createUserMapping().catch(console.error);
