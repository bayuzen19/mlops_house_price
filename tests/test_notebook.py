import gc
import json
import shutil
from pathlib import Path

import yaml
from sklearn.utils import Bunch
from sqlalchemy.engine import Engine


def test_notebook_uses_shared_modules_end_to_end(tmp_path, frame, monkeypatch):
    project = Path(__file__).resolve().parents[1]
    notebook = json.loads((project / "notebooks" / "experiments.ipynb").read_text(encoding="utf-8"))
    shutil.copy2(project / "pyproject.toml", tmp_path / "pyproject.toml")
    (tmp_path / "src" / "house_price").mkdir(parents=True)
    (tmp_path / "notebooks").mkdir()
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    frame.to_csv(raw / "california_housing.csv", index=False)
    config = {
        "training": {"cv": 2, "n_jobs": 1, "param_grid": {"n_estimators": [3]}},
        "mlflow": {"experiment_name": "notebook-test", "registered_model_name": None},
    }
    (tmp_path / "params.yaml").write_text(yaml.safe_dump(config))
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs" / "quick.yaml").write_text(yaml.safe_dump(config))
    monkeypatch.chdir(tmp_path / "notebooks")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    namespace = {}
    try:
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                exec("".join(cell["source"]), namespace)
        result = namespace["result"]
        assert Path(result["local_model_path"]).is_dir()
        assert namespace["dataset"].sha256 == result["dataset_sha256"]
        mse = namespace["mean_squared_error"](namespace["y_test"], namespace["y_pred_loaded"])
        assert mse == result["metrics"]["mse"]
    finally:
        for obj in gc.get_objects():
            if isinstance(obj, Engine):
                obj.dispose()


def test_all_in_one_notebook_trains_and_reloads_without_project_imports(
    tmp_path_factory, frame, monkeypatch
):
    project = Path(__file__).resolve().parents[1]
    notebook = json.loads(
        (project / "notebooks" / "experiments_all_in_one.ipynb").read_text(encoding="utf-8")
    )
    root = tmp_path_factory.mktemp("allinone")
    (root / "notebooks").mkdir()
    monkeypatch.chdir(root / "notebooks")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(root / 'mlflow.db').as_posix()}")
    monkeypatch.setattr(
        "sklearn.datasets.fetch_california_housing",
        lambda **kwargs: Bunch(frame=frame.copy()),
    )
    namespace = {}
    try:
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                assert "from house_price" not in source
                assert "import house_price" not in source
                exec(source, namespace)
        assert (root / ".dvc").is_dir()
        assert namespace["DVC_PATH"].is_file()
        assert namespace["RUN_REPORT_PATH"].is_file()
        assert namespace["loaded_best_model"] is not namespace["best_model"]
        report = json.loads(namespace["RUN_REPORT_PATH"].read_text(encoding="utf-8"))
        assert report["dataset_sha256"] == namespace["dataset_sha256"]
        assert len(namespace["sample_input"]) == 5
        # The notebook itself asserts equality before/after both model loads.
        assert namespace["best_model"].named_steps["scaler"].n_samples_seen_ == len(
            namespace["X_train"]
        )
    finally:
        for obj in gc.get_objects():
            if isinstance(obj, Engine):
                obj.dispose()
