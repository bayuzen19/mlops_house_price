import subprocess

import pytest

from house_price.data import load_dataset
from house_price.versioning import run_dvc, track_data


def test_dvc_restores_dataset(tmp_path, frame):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    run_dvc(tmp_path, "init")
    path = tmp_path / "housing.csv"
    frame.to_csv(path, index=False)
    track_data(tmp_path, path)
    original_bytes = path.read_bytes()
    original_metadata = path.with_suffix(".csv.dvc").read_bytes()
    assert load_dataset(path).dvc_metadata is not None
    frame.loc[0, "MedHouseVal"] += 1
    frame.to_csv(path, index=False)
    track_data(tmp_path, path)
    assert path.with_suffix(".csv.dvc").read_bytes() != original_metadata
    path.with_suffix(".csv.dvc").write_bytes(original_metadata)
    run_dvc(tmp_path, "checkout", "housing.csv.dvc")
    assert path.read_bytes() == original_bytes
    assert run_dvc(tmp_path, "status", "--json") == "{}"


def test_tracking_rejects_external_path(tmp_path):
    with pytest.raises(ValueError, match="di dalam"):
        track_data(tmp_path, tmp_path.parent / "outside.csv")
