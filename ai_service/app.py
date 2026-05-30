import os
from typing import List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from tensorflow.keras.models import load_model


class PredictRequest(BaseModel):
    # Accept one lead (1000 values) or flattened multi-lead data.
    ecg: List[float] = Field(..., min_items=100)
    threshold: Optional[float] = 0.5


class PredictResponse(BaseModel):
    mi_probability: float
    predicted_label: str
    threshold: float


app = FastAPI(title="ECG AI Service", version="1.0.0")

MODEL_PATH = os.getenv("MODEL_PATH", "models/ecg_model.keras")
SCALER_PATH = os.getenv("SCALER_PATH", "models/scaler.pkl")

model = None
scaler = None


@app.on_event("startup")
def startup_load_assets() -> None:
    global model
    global scaler

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Model file not found at {MODEL_PATH}. "
            "Export your trained model from the notebook first."
        )

    model = load_model(MODEL_PATH)

    if os.path.exists(SCALER_PATH):
        scaler = joblib.load(SCALER_PATH)


def _prepare_input(ecg_values: List[float]) -> np.ndarray:
    x = np.array(ecg_values, dtype=np.float32)

    if x.ndim != 1:
        raise HTTPException(status_code=400, detail="ecg must be a 1D numeric list")

    # Default input shape for your notebook models is (batch, 1000, channels).
    # If a single lead is provided, shape it to (1, 1000, 1).
    # If flattened multi-lead is provided (e.g., 12000), reshape to (1, 1000, 12).
    if x.size == 1000:
        x = x.reshape(1, 1000, 1)
    elif x.size == 12000:
        x = x.reshape(1, 1000, 12)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported ecg length. Use 1000 (single lead) or 12000 (12 leads x 1000).",
        )

    if scaler is not None:
        flat = x.reshape(1, -1)
        flat = scaler.transform(flat)
        x = flat.reshape(x.shape)

    return x


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "ecg-ai", "model_path": MODEL_PATH}


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest) -> PredictResponse:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    x = _prepare_input(payload.ecg)

    y = model.predict(x, verbose=0)
    proba = float(np.ravel(y)[0])

    threshold = float(payload.threshold or 0.5)
    label = "MI" if proba >= threshold else "Normal"

    return PredictResponse(
        mi_probability=proba,
        predicted_label=label,
        threshold=threshold,
    )
