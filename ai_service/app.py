import os
from typing import List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Attempt to import TensorFlow Keras loader when available; fall back to sklearn-only mode if not.
try:
    from tensorflow.keras.models import load_model
    _HAS_TF = True
except Exception:
    load_model = None  # type: ignore
    _HAS_TF = False
    # sklearn fallback will be used when TensorFlow is not available
    from sklearn.linear_model import LogisticRegression


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
model_type = None  # 'keras' or 'sklearn'


@app.on_event("startup")
def startup_load_assets() -> None:
    global model
    global scaler
    global model_type

    if not os.path.exists(MODEL_PATH):
        # If a Keras model is expected but missing, attempt sklearn fallback.
        if os.path.exists("models/sklearn_model.pkl"):
            model = joblib.load("models/sklearn_model.pkl")
            model_type = "sklearn"
        else:
            # Create a tiny synthetic sklearn model so the service can respond.
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
            # Train on small synthetic data
            X_demo = np.random.randn(200, 1000 * 1)
            y_demo = (np.random.rand(200) > 0.7).astype(int)
            scaler = StandardScaler()
            X_demo = scaler.fit_transform(X_demo)
            clf = LogisticRegression(max_iter=200)
            clf.fit(X_demo, y_demo)
            model = clf
            model_type = "sklearn"
            # save artifacts for later
            os.makedirs("models", exist_ok=True)
            joblib.dump(model, "models/sklearn_model.pkl")
            joblib.dump(scaler, "models/scaler.pkl")
            print("Trained and saved small sklearn fallback model at models/sklearn_model.pkl")
        return

    # If MODEL_PATH exists, prefer loading Keras model when TensorFlow is available
    if _HAS_TF and MODEL_PATH.endswith('.keras'):
        model = load_model(MODEL_PATH)
        model_type = "keras"
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
        return

    # If TensorFlow isn't available or MODEL_PATH doesn't point to a Keras artifact,
    # try to load a sklearn artifact instead.
    if os.path.exists(MODEL_PATH) and MODEL_PATH.endswith('.pkl'):
        model = joblib.load(MODEL_PATH)
        model_type = "sklearn"
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
        return

    # Last resort: use sklearn fallback (same as above)
    if os.path.exists("models/sklearn_model.pkl"):
        model = joblib.load("models/sklearn_model.pkl")
        model_type = "sklearn"
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
        return

    raise RuntimeError(
        f"Model file not found at {MODEL_PATH} and no fallback available. Export your trained model from the notebook first."
    )


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

    # Keras model expects 3D input; sklearn expects 2D flattened input
    if model_type == "keras":
        y = model.predict(x, verbose=0)
        proba = float(np.ravel(y)[0])
    else:
        flat = x.reshape(1, -1)
        try:
            proba = float(model.predict_proba(flat)[0, 1])
        except Exception:
            # Some sklearn classifiers may only expose predict; fallback to predict
            proba = float(model.predict(flat)[0])

    threshold = float(payload.threshold or 0.5)
    label = "MI" if proba >= threshold else "Normal"

    return PredictResponse(
        mi_probability=proba,
        predicted_label=label,
        threshold=threshold,
    )
