import gc
import hashlib

import numpy as np
import pandas as pd
import pytest
import yaml
from sqlalchemy.engine import Engine

from house_price.config import TrainingConfig
from house_price.data import FEATURES, TARGET
from house_price.train import local_tracking_uri, train_model


@pytest.fixture
def frame():
    rng = np.random.default_rng(42)
    result = pd.DataFrame(rng.normal(size=(80, len(FEATURES))), columns=FEATURES)
    result[TARGET] = 2 + result["MedInc"] * 0.3 + result["HouseAge"] * 0.1
    return result


@pytest.fixture
def data_path(tmp_path, frame):
    path = tmp_path / "housing.csv"
    frame.to_csv(path, index=False)
    content = path.read_bytes()
    metadata = {
        "outs": [
            {
                "path": path.name,
                "hash": "md5",
                "size": len(content),
                "md5": hashlib.md5(content, usedforsecurity=False).hexdigest(),
            }
        ]
    }
    path.with_suffix(".csv.dvc").write_text(yaml.safe_dump(metadata), encoding="utf-8")
    return path


@pytest.fixture
def small_config():
    return TrainingConfig(
        cv=2,
        n_jobs=1,
        param_grid={"n_estimators": [3, 5], "max_depth": [3]},
        experiment_name="pytest",
        registered_model_name="pytest-house-price",
    )


@pytest.fixture
def trained(tmp_path, data_path, small_config):
    uri = local_tracking_uri(tmp_path / "tracking")
    result = train_model(data_path, tmp_path / "output", small_config, tracking_uri=uri)
    yield result, uri
    for obj in gc.get_objects():
        if isinstance(obj, Engine):
            obj.dispose()
