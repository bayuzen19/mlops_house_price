import gc
import json
import shutil
from pathlib import Path

import yaml
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
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
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
