import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from house_price.data import FEATURES, TARGET, load_dataset, prepare_data, validate_features


def test_loaded_data_matches_recorded_bytes(data_path):
    dataset = load_dataset(data_path)
    assert dataset.sha256 == hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert dataset.frame.shape == (80, 9)
    assert dataset.dvc_metadata is not None


def test_modified_csv_is_rejected_before_training(data_path):
    data_path.write_bytes(data_path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="berbeda dari versi DVC"):
        load_dataset(data_path)


def test_dvc_metadata_required_by_default(data_path):
    data_path.with_suffix(".csv.dvc").unlink()
    with pytest.raises(FileNotFoundError, match="Metadata belum ada"):
        load_dataset(data_path)
    assert load_dataset(data_path, require_dvc=False).dvc_metadata is None


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
def test_invalid_feature_values_rejected(frame, bad_value):
    frame.loc[0, FEATURES[0]] = bad_value
    with pytest.raises(ValueError, match="NaN"):
        validate_features(frame)


def test_missing_feature_rejected(frame):
    with pytest.raises(ValueError, match="tidak lengkap"):
        validate_features(frame.drop(columns=[FEATURES[0]]))


def test_feature_order_is_canonical(frame):
    reordered = frame[list(reversed(FEATURES))]
    assert validate_features(reordered).columns.tolist() == FEATURES


def test_prepare_preserves_existing_bytes(data_path):
    before = data_path.read_bytes()
    assert prepare_data(data_path) == data_path
    assert data_path.read_bytes() == before


def test_prepare_does_not_replace_a_missing_dvc_version(data_path):
    data_path.unlink()
    with pytest.raises(FileNotFoundError, match="dvc checkout"):
        prepare_data(data_path)


def test_explicit_bootstrap_restores_exact_snapshot(data_path, frame, monkeypatch):
    expected = data_path.read_bytes()
    data_path.unlink()
    monkeypatch.setattr(
        "house_price.data.fetch_california_housing",
        lambda **_: SimpleNamespace(frame=frame),
    )
    prepare_data(data_path, from_source=True)
    assert data_path.read_bytes() == expected
    load_dataset(data_path)


def test_bootstrap_refuses_a_different_version(data_path, frame, monkeypatch):
    data_path.unlink()
    frame.loc[0, TARGET] += 1
    monkeypatch.setattr(
        "house_price.data.fetch_california_housing",
        lambda **_: SimpleNamespace(frame=frame),
    )
    with pytest.raises(ValueError, match="tidak cocok"):
        prepare_data(data_path, from_source=True)
    assert not data_path.exists()


def test_missing_target_rejected(tmp_path, frame):
    path = tmp_path / "no-target.csv"
    frame.drop(columns=TARGET).to_csv(path, index=False)
    with pytest.raises(ValueError, match="target numerik"):
        load_dataset(path, require_dvc=False)
