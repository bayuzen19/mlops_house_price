"""Offline container test: train, save, load, and predict on synthetic data."""

import gc
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from house_price.config import TrainingConfig
from house_price.data import FEATURES, TARGET
from house_price.predict import load_model, predict
from house_price.train import local_tracking_uri, train_model


def main():
    with tempfile.TemporaryDirectory(prefix="house-price-smoke-") as directory:
        root = Path(directory).resolve()
        assert root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        try:
            rng = np.random.default_rng(42)
            frame = pd.DataFrame(rng.normal(size=(80, len(FEATURES))), columns=FEATURES)
            frame[TARGET] = 2 + frame["MedInc"] * 0.3 + frame["HouseAge"] * 0.1
            data = root / "synthetic.csv"
            frame.to_csv(data, index=False)
            config = TrainingConfig(
                cv=2,
                n_jobs=1,
                param_grid={"n_estimators": [3], "max_depth": [3]},
                experiment_name="offline-smoke",
                registered_model_name=None,
            )
            uri = local_tracking_uri(root / "tracking")
            result = train_model(data, root / "output", config, tracking_uri=uri, require_dvc=False)
            remote = load_model(result["model_uri"], tracking_uri=uri)
            exported = load_model(result["local_model_path"])
            np.testing.assert_array_equal(
                predict(remote, frame)["prediction"],
                predict(exported, frame)["prediction"],
            )
            assert np.isfinite(list(result["metrics"].values())).all()
            print("PASS: offline training, MLflow load, exported model, and raw-data prediction.")
        finally:
            # Release SQLite handles before TemporaryDirectory cleanup on Windows.
            for obj in gc.get_objects():
                if isinstance(obj, Engine):
                    obj.dispose()


if __name__ == "__main__":
    main()
