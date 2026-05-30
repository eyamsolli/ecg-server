"""
Run this after training in your notebook session, or adapt it inside a notebook cell.
It exports the trained Keras model and optional scaler for Render deployment.
"""

from pathlib import Path

import joblib

# Expected globals if run inside notebook kernel:
# - models (dict), e.g. models['CNN']
# - scaler (optional)

OUTPUT_DIR = Path("ai_service/models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if "models" not in globals():
    raise RuntimeError("'models' dictionary is not available. Run training first.")

# Pick the model key you want to deploy.
MODEL_KEY = "CNN"
if MODEL_KEY not in models:
    raise RuntimeError(f"Model key '{MODEL_KEY}' not found. Available: {list(models.keys())}")

keras_model = models[MODEL_KEY]
keras_model.save(OUTPUT_DIR / "ecg_model.keras")
print("Saved model:", OUTPUT_DIR / "ecg_model.keras")

if "scaler" in globals() and scaler is not None:
    joblib.dump(scaler, OUTPUT_DIR / "scaler.pkl")
    print("Saved scaler:", OUTPUT_DIR / "scaler.pkl")
else:
    print("No scaler found in globals(); scaler export skipped.")
