import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from house_price.versioning import run_dvc, track_data


def test_dvc_pipeline_reproduces_and_caches(tmp_path_factory, frame, monkeypatch):
    # DVC run-cache paths include two long hashes; keep the Windows test root short.
    tmp_path = tmp_path_factory.mktemp("dvc")
    project = Path(__file__).resolve().parents[1]
    for name in ("pyproject.toml", "dvc.yaml", ".dvcignore"):
        shutil.copy2(project / name, tmp_path / name)
    shutil.copytree(
        project / "src" / "house_price",
        tmp_path / "src" / "house_price",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    run_dvc(tmp_path, "init")
    data = tmp_path / "data" / "raw" / "california_housing.csv"
    data.parent.mkdir(parents=True)
    frame.to_csv(data, index=False)
    track_data(tmp_path, data)
    config = {
        "training": {"cv": 2, "n_jobs": 1, "param_grid": {"n_estimators": [3]}},
        "mlflow": {"experiment_name": "dvc-test", "registered_model_name": None},
    }
    (tmp_path / "params.yaml").write_text(yaml.safe_dump(config))
    monkeypatch.setenv("PATH", str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)
    run_dvc(tmp_path, "repro")
    assert (tmp_path / "dvc.lock").exists()
    output = tmp_path / "artifacts" / "training"
    report = json.loads((output / "run.json").read_text())
    assert (output / "model" / "MLmodel").exists()
    run_dvc(tmp_path, "repro")
    assert json.loads((output / "run.json").read_text())["run_id"] == report["run_id"]
    assert run_dvc(tmp_path, "status", "--json") == "{}"
    config["training"]["param_grid"]["n_estimators"] = [4]
    (tmp_path / "params.yaml").write_text(yaml.safe_dump(config))
    run_dvc(tmp_path, "repro")
    updated = json.loads((output / "run.json").read_text())
    assert updated["run_id"] != report["run_id"]
    assert updated["best_params"]["n_estimators"] == 4
    assert run_dvc(tmp_path, "status", "--json") == "{}"
