"""Load the saved pipeline and predict directly from unscaled features."""

import mlflow
import mlflow.sklearn
import pandas as pd

from house_price.data import validate_features


def load_model(model_uri: str, *, tracking_uri: str | None = None):
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    return mlflow.sklearn.load_model(model_uri)


def predict(model, frame: pd.DataFrame) -> pd.DataFrame:
    features = validate_features(frame)
    return pd.DataFrame({"prediction": model.predict(features)}, index=frame.index)
