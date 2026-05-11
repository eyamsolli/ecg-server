# Deploy to Render

## Step 1: Prepare values

Get your service account JSON and extract the needed values:

```powershell
# Read the JSON
$json = Get-Content .\serviceAccountKey.json -Raw
Write-Host $json

# Extract the project ID (you'll see it in the JSON)
# From serviceAccountKey.json: "project_id": "test-55a6a"
```

You need:
- **FIREBASE_SERVICE_ACCOUNT** = the entire `serviceAccountKey.json` content as a single string
- **FIREBASE_DATABASE_URL** = `https://test-55a6a-default-rtdb.firebaseio.com`
- **API_KEY** = `mysecret` (or any secret you choose)

## Step 2: Go to Render Dashboard

1. Open https://dashboard.render.com/
2. Find your service `ecg-server-66sa` (or create one if missing)
3. Click on it to open settings

## Step 3: Set Environment Variables

1. Go to **Environment** tab
2. Click **Add Environment Variable**
3. Paste these (one by one):

**Variable 1:**
- Name: `FIREBASE_SERVICE_ACCOUNT`
- Value: Copy the entire contents of `serviceAccountKey.json` (the raw JSON string)
  ```
  {"type":"service_account","project_id":"test-55a6a",...}
  ```

**Variable 2:**
- Name: `FIREBASE_DATABASE_URL`
- Value: 
  ```
  https://test-55a6a-default-rtdb.firebaseio.com
  ```

**Variable 3:**
- Name: `API_KEY`
- Value:
  ```
  mysecret
  ```

## Step 4: Commit and Push

Render auto-deploys on git push. Make sure your repo is up to date:

```powershell
git add .
git commit -m "Add Firebase RTDB integration with env var config"
git push origin main
```

Or push from Render's UI if your repo is connected.

## Step 5: Wait for Render Redeploy

Monitor the Render deploy page. You should see:
- Build succeeds
- Server starts and logs `[Firebase] Connected to Realtime Database`
- Listens on the assigned port (usually 3000 or a forwarded port)

## Step 6: Test the Live Endpoint

Once deployed, test with PowerShell:

```powershell
Invoke-RestMethod -Uri 'https://ecg-server-66sa.onrender.com/ecg' `
  -Method Post `
  -ContentType 'application/json' `
  -Headers @{ 'x-api-key' = 'mysecret' } `
  -Body ( @{ ecg = 512 } | ConvertTo-Json )
```

You should get back a response with a saved record ID (e.g., `"id":"-OsN0_sxbEUTYJSxLnV8"`).

## Step 7: Verify Data in Firebase

1. Go to Firebase Console: https://console.firebase.google.com/project/test-55a6a/database/
2. Click on the Realtime Database
3. Look for `/ecg_readings` — you should see your POSTed data there

## If Deploy Fails

Check Render logs:
1. Render dashboard → your service → **Logs** tab
2. Common issues:
   - `FIREBASE_SERVICE_ACCOUNT` is malformed JSON (newlines not escaped)
   - `FIREBASE_DATABASE_URL` is wrong or empty
   - Service account has no Realtime DB permissions (check Firebase IAM)

If Render rejects newlines in the JSON, try base64 encoding:

```powershell
# Base64 encode the JSON
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content .\serviceAccountKey.json -Raw)))
Write-Host $b64

# Set as FIREBASE_SERVICE_ACCOUNT_B64 in Render
# Then modify server.js start to decode it (uncomment the fallback in server.js if needed)
```

## Next: Test from SIM7000E

Once Render is live, update your SIM7000E client to POST to:
```
https://ecg-server-66sa.onrender.com/ecg
```

With headers:
```
Content-Type: application/json
x-api-key: mysecret
```

Body:
```json
{"ecg": 512}
```
