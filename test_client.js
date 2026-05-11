// Simple test client to POST ECG readings to local server
const url = process.env.SERVER_URL || 'http://localhost:3000/ecg';
const apiKey = process.env.API_KEY || 'mysecret';

async function postReading(payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
    },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  console.log('status', res.status, 'body', text);
}

async function main() {
  const payload = { ecg: 512, timestamp: new Date().toISOString() };
  await postReading(payload);
}

main().catch(err => { console.error(err); process.exit(1); });
