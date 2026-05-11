# ECG Backend (SIM7000E → Node → Firebase Realtime DB)

This project receives ECG readings from a SIM7000E (or any HTTP client) and writes them to Firebase Realtime Database.

Quick start (local)

1. Install dependencies

```bash
npm install
```

2. Set env vars for Render or override local defaults

```powershell
# Local development can use `serviceAccountKey.json` automatically.
# On Render, set FIREBASE_SERVICE_ACCOUNT and FIREBASE_DATABASE_URL.
$env:FIREBASE_SERVICE_ACCOUNT = Get-Content .\serviceAccountKey.json -Raw
$env:FIREBASE_DATABASE_URL = 'https://test-55a6a-default-rtdb.firebaseio.com'
$env:API_KEY = 'mysecret'
node server.js
```

3. Test locally (PowerShell)

```powershell
Invoke-RestMethod -Uri 'http://localhost:3000/ecg' -Method Post -ContentType 'application/json' -Headers @{ 'x-api-key' = 'mysecret' } -Body ( @{ ecg = 512 } | ConvertTo-Json )
```

Or using `curl.exe` from PowerShell:

```powershell
& curl.exe -X POST "http://localhost:3000/ecg" -H "Content-Type: application/json" -H "x-api-key: mysecret" -d "{\"ecg\":512}"
```

Simulated device (Node)

```bash
node test_client.js
```

Render deployment notes

- On Render, create a Web Service and connect your repo. Set the start command to `npm start`.
- Add environment variables in Render's dashboard:
  - `FIREBASE_SERVICE_ACCOUNT` — the full JSON service account string (paste entire JSON). If Render complains about newlines, base64-encode the JSON and decode at runtime:

    ```powershell
    $b = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content .\serviceAccountKey.json -Raw)))
    # paste $b into Render as FIREBASE_SERVICE_ACCOUNT_B64
    # then on Render start command: node -e "process.env.FIREBASE_SERVICE_ACCOUNT=Buffer.from(process.env.FIREBASE_SERVICE_ACCOUNT_B64,'base64').toString(); require('./server.js')"
    ```

  - `FIREBASE_DATABASE_URL` — your RTDB URL (e.g. `https://test-55a6a-default-rtdb.firebaseio.com`)
  - `API_KEY` — optional device secret

Local fallback

- If `FIREBASE_SERVICE_ACCOUNT` is not set locally, the server reads `serviceAccountKey.json` from the project root and derives the default RTDB URL from the project ID.
- This fallback is for development only; keep the JSON file out of Render and other shared deployments.

Security

- Use `API_KEY` to authenticate devices (server checks `x-api-key`, `api_key` body or query).
- For production, enable HTTPS on your Render service (Render provides TLS by default) and consider per-device credentials or OAuth.

SIM7000E examples

- See `SIM7000E_client_example.md` for an Arduino + TinyGSM sketch and quick AT-note.

Where to look for issues

- Server logs (Render dashboard or local console) for Firebase write errors.
- Firebase Console → Realtime Database → view `/ecg_readings` for incoming data.

If you want, I can: deploy these Render env vars for you (instructions), add TLS-enforced callbacks, or add per-device keys and a registration endpoint.# ecg-server