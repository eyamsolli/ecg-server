console.log("🔥 SERVER STARTING - ECG ROUTE LOADING");

const express = require("express");
const admin = require("firebase-admin");

const app = express();

// Firebase credentials from Render environment variable
const serviceAccount = JSON.parse(process.env.FIREBASE_KEY);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://test-55a6a-default-rtdb.firebaseio.com"
});

const db = admin.database();

app.use(express.json());

// Health route
app.get("/", (req, res) => {
  res.send("ECG SERVER REDEPLOY FIXED v4");
});

// ECG route
app.post("/ecg", async (req, res) => {
  try {
    const ecgValue = req.body.ecg;

    await db.ref("ecg/device1").push({
      value: ecgValue,
      timestamp: Date.now()
    });

    console.log("Received ECG:", ecgValue);

    res.status(200).send("OK");

  } catch (error) {
    console.error(error);
    res.status(500).send("ERROR");
  }
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`ECG server running on port ${PORT}`);
  console.log("ROUTES READY: / and /ecg");
});