const express = require("express");
const admin = require("firebase-admin");
app.get("/", (req, res) => {
  res.send("ECG server is running");
});
// Firebase credentials from Render environment variable
const serviceAccount = JSON.parse(process.env.FIREBASE_KEY);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://test-55a6a-default-rtdb.firebaseio.com"
});

const db = admin.database();

const app = express();

app.use(express.json());

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

// Render-compatible port
const PORT = process.env.PORT || 3000;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`ECG server running on port ${PORT}`);
});