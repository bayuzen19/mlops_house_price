"""Fit one preprocessing/model pipeline and persist its data lineage."""

import json
import os
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from house_price.config import TrainingConfig
from house_price.data import FEATURES, TARGET, load_dataset

TRUSTED_TYPES = ["sklearn.tree._tree.Tree"]


def local_tracking_uri(root: str | Path) -> str:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(root / 'mlflow.db').as_posix()}"


def train_model(
    data_path: str | Path,
    output_dir: str | Path,
    config: TrainingConfig,
    *,
    tracking_uri: str | None = None,
    require_dvc: bool = True,
) -> dict:
    data_path, output_dir = Path(data_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists() and any(item.name != ".gitignore" for item in output_dir.iterdir()):
        raise FileExistsError(f"Folder output tidak kosong: {output_dir}. Pilih folder baru.")
    dataset = load_dataset(data_path, require_dvc=require_dvc)
    frame = dataset.frame
    X_train, X_test, y_train, y_test = train_test_split(
        frame[FEATURES],
        frame[TARGET],
        test_size=config.test_size,
        random_state=config.random_state,
    )
    if len(X_train) < config.cv or len(X_test) < 2:
        raise ValueError("Jumlah data tidak cukup untuk cross-validation dan evaluasi R2.")
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", RandomForestRegressor(random_state=config.random_state, n_jobs=1)),
        ]
    )
    search = GridSearchCV(
        pipeline,
        {f"model__{key}": values for key, values in config.param_grid.items()},
        cv=config.cv,
        scoring="neg_mean_squared_error",
        n_jobs=config.n_jobs,
        error_score="raise",
    )
    selected_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    if selected_uri is None:
        selected_uri = local_tracking_uri(Path.cwd() / ".mlflow")
    mlflow.set_tracking_uri(selected_uri)
    if mlflow.get_experiment_by_name(config.experiment_name) is None:
        artifact_location = None
        if selected_uri.startswith("sqlite:///"):
            db_path = Path(selected_uri.removeprefix("sqlite:///"))
            artifact_location = (db_path.parent / "artifacts").resolve().as_uri()
        mlflow.create_experiment(config.experiment_name, artifact_location=artifact_location)
    mlflow.set_experiment(config.experiment_name)
    requirements = [
        f"{name}=={version(name)}"
        for name in ("mlflow", "scikit-learn", "skops", "pandas", "numpy")
    ]
    with mlflow.start_run() as run:
        mlflow.set_tags(
            {
                "dataset.path": data_path.name,
                "dataset.sha256": dataset.sha256,
                "dataset.versioning": "dvc" if dataset.dvc_metadata else "unversioned",
            }
        )
        if dataset.dvc_metadata:
            mlflow.log_text(dataset.dvc_metadata, f"data_version/{data_path.name}.dvc")
        mlflow.log_dict(asdict(config), "training_config.json")
        mlflow.log_params(
            {
                "split_random_state": config.random_state,
                "test_size": config.test_size,
                "cv": config.cv,
                "training_rows": len(X_train),
                "test_rows": len(X_test),
            }
        )
        search.fit(X_train, y_train)
        best_model = search.best_estimator_
        predictions = best_model.predict(X_test)
        mse = float(mean_squared_error(y_test, predictions))
        metrics = {
            "mse": mse,
            "rmse": float(np.sqrt(mse)),
            "r2_score": float(r2_score(y_test, predictions)),
            "cv_mse": float(-search.best_score_),
        }
        best_params = {key.removeprefix("model__"): val for key, val in search.best_params_.items()}
        mlflow.log_params({f"best_{key}": val for key, val in best_params.items()})
        mlflow.log_metrics(metrics)
        signature = infer_signature(X_train, best_model.predict(X_train))
        model_options = {
            "signature": signature,
            "input_example": X_train.head(3),
            "serialization_format": "skops",
            "skops_trusted_types": TRUSTED_TYPES,
            "pip_requirements": requirements,
        }
        info = mlflow.sklearn.log_model(
            best_model,
            name="model",
            registered_model_name=config.registered_model_name,
            **model_options,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        mlflow.sklearn.save_model(best_model, path=str(output_dir / "model"), **model_options)
        result = {
            "run_id": run.info.run_id,
            "model_uri": info.model_uri,
            "local_model_path": str(output_dir / "model"),
            "dataset_sha256": dataset.sha256,
            "metrics": metrics,
            "best_params": best_params,
        }
        (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        (output_dir / "run.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
