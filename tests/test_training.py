import json
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from house_price.cli import main
from house_price.data import FEATURES, TARGET, load_dataset
from house_price.predict import load_model, predict
from house_price.train import train_model


def test_training_lineage_pipeline_and_cli(trained, data_path, small_config, tmp_path):
    result, uri = trained
    dataset = load_dataset(data_path)
    client = mlflow.MlflowClient(tracking_uri=uri)
    run = client.get_run(result["run_id"])
    assert run.info.status == "FINISHED"
    assert run.data.tags["dataset.sha256"] == dataset.sha256
    assert run.data.tags["dataset.versioning"] == "dvc"
    artifact = client.download_artifacts(run.info.run_id, f"data_version/{data_path.name}.dvc")
    assert Path(artifact).read_text(encoding="utf-8") == dataset.dvc_metadata
    model = load_model(result["model_uri"], tracking_uri=uri)
    exported = load_model(result["local_model_path"])
    registered = load_model("models:/pytest-house-price/1", tracking_uri=uri)
    expected = predict(model, dataset.frame)
    np.testing.assert_array_equal(expected, predict(exported, dataset.frame))
    np.testing.assert_array_equal(expected, predict(registered, dataset.frame))
    # Scaler must have been fitted on the training split, not the held-out test data.
    X_train, _, _, _ = train_test_split(
        dataset.frame[FEATURES],
        dataset.frame[TARGET],
        test_size=small_config.test_size,
        random_state=small_config.random_state,
    )
    np.testing.assert_allclose(model.named_steps["scaler"].mean_, X_train.mean())
    assert np.isfinite(list(result["metrics"].values())).all()
    report = json.loads((tmp_path / "output" / "run.json").read_text())
    assert report["model_uri"] == result["model_uri"]
    output = tmp_path / "predictions.csv"
    assert (
        main(
            [
                "predict",
                "--model-uri",
                result["local_model_path"],
                "--input",
                str(data_path),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    np.testing.assert_allclose(pd.read_csv(output)["prediction"], expected["prediction"])
    with pytest.raises(FileExistsError):
        main(
            [
                "predict",
                "--model-uri",
                result["local_model_path"],
                "--input",
                str(data_path),
                "--output",
                str(output),
            ]
        )


def test_training_preserves_existing_output(tmp_path, data_path, small_config):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "previous-run.txt"
    sentinel.write_text("keep me")
    with pytest.raises(FileExistsError):
        train_model(data_path, output, small_config)
    assert sentinel.read_text() == "keep me"
