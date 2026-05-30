# Deploy ECG AI to Render

This guide deploys your notebook-trained ECG classifier as a live API on Render.

## 1) Export model artifacts from notebook

Your notebook currently trains models but does not save a deployable artifact by default.

1. Open the notebook:
   - FINAL2 final PTB-XL TEST.ipynb
2. Run training so `models` (and optionally `scaler`) exist in memory.
3. Run the export snippet in `ai_service/export_model_snippet.py` inside the notebook kernel (or copy its code into a notebook cell).
4. Confirm these files exist:
   - `ai_service/models/ecg_model.keras`
   - `ai_service/models/scaler.pkl` (optional)

Important:
- If `ecg_model.keras` is very large (>100MB), use Git LFS or host it in cloud storage and download at startup.

## 2) Commit and push

From the repo root:

```powershell
git add ai_service DEPLOY_AI_RENDER.md
git commit -m "Add Render-ready ECG AI inference service"
git push origin main
```

## 3) Create Render Web Service

1. Go to Render dashboard.
2. New + -> Web Service.
3. Select your GitHub repo.
4. Configure:
   - Root Directory: `ai_service`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

Or use blueprint from `ai_service/render.yaml`.

## 4) Environment variables in Render

Set these in Render service settings:

- `MODEL_PATH= models/ecg_model.keras`
- `SCALER_PATH= models/scaler.pkl` (optional)

## 5) Health check and test

After deploy:

- GET `/health` should return model status.
- POST `/predict` example:

```json
{
  "ecg": [0.01, 0.03, -0.02, 0.1],
  "threshold": 0.5
}
```

Note: for your current model shape, send either:
- 1000 values (single lead), or
- 12000 values (12 leads x 1000 flattened)

## 6) Optional: connect your existing Node backend

You can keep your current Node ingestion server and call this AI service from it.
Recommended env var in Node service:
- `AI_SERVICE_URL=https://your-ai-service.onrender.com/predict`

Then forward ECG data after write to Firebase.
