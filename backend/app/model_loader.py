"""XGBoost model loading and inference."""

import joblib

from .config import CITIES, MODEL_DIR, MODEL_II_FEATURES

# In-memory cache — models loaded once at startup
_models: dict[str, object] = {}


def get_model(city: str):
    """Load and cache the XGBoost .pkl model for the given city."""
    # Normalize the city key to match the CITIES dictionary.
    city_key = city.lower()
    if city_key not in CITIES:
        raise ValueError(f"Unknown city: {city}")

    # Lazy-load if startup did not preload the model, then keep it in memory.
    if city_key not in _models:
        model_path = MODEL_DIR / CITIES[city_key]["model_file"]
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        _models[city_key] = joblib.load(model_path)

    return _models[city_key]


def predict(city: str, feature_df) -> list[float]:
    """Run XGBoost inference and clamp negative irradiance to zero."""
    model = get_model(city)
    # Select/reorder the columns exactly as the trained model expects.
    predictions = model.predict(feature_df[MODEL_II_FEATURES])
    # Solar irradiance cannot be negative, so clamp impossible model outputs.
    return [max(0.0, float(value)) for value in predictions]
