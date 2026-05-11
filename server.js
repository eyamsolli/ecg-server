const express = require("express");
const admin = require("firebase-admin");
const fs = require("fs");
const path = require("path");

// ─── 1. App setup ────────────────────────────────────────────────────────────
const app = express();
app.use(express.json());                        // parse JSON bodies
app.use(express.urlencoded({ extended: true })); // parse form-encoded bodies (SIM7000 fallback)

// ─── 2. Firebase setup ───────────────────────────────────────────────────────
//  serviceAccountKey is injected as an env var on Render (never commit the file)
let db = null;
try {
  const serviceAccountJson = process.env.FIREBASE_SERVICE_ACCOUNT || fs.readFileSync(path.join(__dirname, "serviceAccountKey.json"), "utf8");
  const serviceAccount = JSON.parse(serviceAccountJson);
  const databaseURL = process.env.FIREBASE_DATABASE_URL || `https://${serviceAccount.project_id}-default-rtdb.firebaseio.com`;
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL,
  });
  db = admin.database();
  console.log("[Firebase] Connected to Realtime Database");
} catch (err) {
  console.error("[Firebase] Init failed — check FIREBASE_SERVICE_ACCOUNT or serviceAccountKey.json:", err.message);
}

// ─── 3. Routes (MUST come after middleware, before error handler) ─────────────

// Health check — confirms Express is alive
app.get("/", (req, res) => {
  res.json({ status: "ok", message: "ECG backend running" });
});

// DEBUG: mirror back anything that hits /ecg — remove after confirming route works
app.all("/ecg", (req, res, next) => {
  console.log(`[/ecg] ${req.method} — body:`, req.body);
  next(); // hand off to the real POST handler below
});

// Main ECG ingestion endpoint
app.post("/ecg", async (req, res) => {
  // If an API key is configured, require it in `x-api-key` header (or query/body)
  if (process.env.API_KEY) {
    const provided = req.get("x-api-key") || req.query.api_key || req.body.api_key;
    if (!provided || provided !== process.env.API_KEY) {
      return res.status(401).json({ error: "Unauthorized" });
    }
  }
  const { ecg, heartRate, spo2, timestamp } = req.body;

  // Validate required field
  if (ecg === undefined || ecg === null) {
    return res.status(400).json({ error: "Missing required field: ecg" });
  }

  const payload = {
    ecg,
    heartRate: heartRate ?? null,
    spo2: spo2 ?? null,
    timestamp: timestamp ?? new Date().toISOString(),
    receivedAt: new Date().toISOString(),
  };

  // Write to Realtime Database (skip gracefully if Firebase didn't initialise)
  if (db) {
    try {
      const ref = db.ref("ecg_readings").push();
      await ref.set(payload);
      console.log("[RTDB] Saved:", ref.key);
      return res.status(201).json({ success: true, id: ref.key, data: payload });
    } catch (err) {
      console.error("[RTDB] Write failed:", err.message);
      return res.status(500).json({ error: "Realtime DB write failed", detail: err.message });
    }
  }

  // Firebase not available — still return 200 so hardware doesn't retry-loop
  console.warn("[/ecg] Firebase unavailable, returning in-memory ack");
  return res.status(200).json({ success: true, warning: "Firebase offline", data: payload });
});

// ─── 4. 404 catch-all (must be last) ─────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: `Cannot ${req.method} ${req.path}` });
});

// ─── 5. Start server (try next port on EADDRINUSE) ────────────────────────────
const DEFAULT_PORT = parseInt(process.env.PORT || '3000', 10);

function startServer(port) {
  const server = app.listen(port, () => {
    console.log(`[Server] Listening on port ${port}`);
    console.log(`[Routes] GET / | POST /ecg`);
  });

  server.on('error', (err) => {
    if (err && err.code === 'EADDRINUSE') {
      console.warn(`[Server] Port ${port} in use — trying ${port + 1}`);
      setTimeout(() => startServer(port + 1), 200);
      return;
    }
    console.error('[Server] Unexpected error', err);
    process.exit(1);
  });
}

startServer(DEFAULT_PORT);