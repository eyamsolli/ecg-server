const express = require("express");
const admin = require("firebase-admin");

const serviceAccount = require("./serviceAccountKey.json");

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
    console.log(error);
    res.status(500).send("ERROR");
  }
});

app.listen(3000, "0.0.0.0", () => {
  console.log("ECG server running on port 3000");
});