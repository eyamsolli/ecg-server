SIM7000E client example (Arduino + TinyGSM)

Overview
- Use TinyGSM + ArduinoHttpClient to POST ECG JSON to your backend (`/ecg`).
- Replace `APN`, `SERVER`, and `API_KEY` with your values.

Wiring / prerequisites
- SIM7000E module wired to a hardware serial or Serial1 on your board.
- Install libraries: `TinyGsm` and `ArduinoHttpClient`.

Example sketch

```cpp
#include <TinyGsmClient.h>
#include <ArduinoHttpClient.h>

#define MODEM_RX  10
#define MODEM_TX  11
#define MODEM_PWR 9

// Serial for modem
HardwareSerial SerialAT(1);
TinyGsm modem(SerialAT);
TinyGsmClient client(modem);

const char* APN = "your.apn.here";
const char* SERVER = "your.server.com"; // or IP
const uint16_t SERVER_PORT = 80;
const char* API_KEY = "REPLACE_WITH_KEY"; // optional

void setup() {
  Serial.begin(115200);
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);

  // Power on modem if needed
  pinMode(MODEM_PWR, OUTPUT);
  digitalWrite(MODEM_PWR, HIGH);

  Serial.println("Initializing modem...");
  if (!modem.init()) {
    Serial.println("Modem init failed");
    while (1) delay(1000);
  }

  Serial.println("Waiting for network...");
  if (!modem.waitForNetwork()) {
    Serial.println("Network fail");
  }

  Serial.println("Connecting to GPRS...");
  if (!modem.gprsConnect(APN, "", "")) {
    Serial.println("GPRS connect failed");
  }
}

void loop() {
  // Build JSON payload (example)
  String payload = "{\"ecg\":512,\"timestamp\":\"" + String(millis()) + "\"}";

  ArduinoHttpClient http(client, SERVER, SERVER_PORT);
  http.beginRequest();
  http.post("/ecg");
  http.sendHeader("Content-Type", "application/json");
  http.sendHeader("Content-Length", payload.length());
  // optional API key header
  http.sendHeader("x-api-key", API_KEY);
  http.beginBody();
  http.print(payload);
  http.endRequest();

  int status = http.responseStatusCode();
  String resp = http.responseBody();
  Serial.print("Status: "); Serial.println(status);
  Serial.print("Resp: "); Serial.println(resp);

  delay(10000);
}
```

Quick curl test (simulate SIM7000E):

```bash
curl -X POST http://localhost:3000/ecg \
  -H "Content-Type: application/json" \
  -H "x-api-key: REPLACE_WITH_KEY" \
  -d '{"ecg":512}'
```

Notes
- For production, secure the endpoint (API key, TLS). Use `FIREBASE_SERVICE_ACCOUNT` and `FIREBASE_DATABASE_URL` env vars on server.
- If you need raw AT command examples instead of TinyGSM, tell me and I'll add them.
