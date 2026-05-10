console.log("🔥 SERVER STARTING");

const express = require("express");
const app = express();

app.use(express.json());

// HEALTH ROUTE FIRST
app.get("/", (req, res) => {
  res.send("ECG SERVER RUNNING OK");
});

// ECG ROUTE FIRST (NO FIREBASE YET)
app.post("/ecg", (req, res) => {
  console.log("ECG HIT:", req.body);
  res.send("OK");
});

// NOW Firebase (after routes)
const admin = require("firebase-admin");

try {
  const serviceAccount = JSON.parse(process.env.FIREBASE_KEY);

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://test-55a6a-default-rtdb.firebaseio.com"
  });

  console.log("🔥 Firebase connected");
} catch (err) {
  console.log("⚠ Firebase failed but server still runs:", err.message);
}

const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log("ECG server running on port", PORT);
});