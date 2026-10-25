"""Prepare and validate data without overwriting an existing dataset."""

import hashlib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.datasets import fetch_california_housing

FEATURES = [
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
]
TARGET = "MedHouseVal"


@dataclass(frozen=True)
class Dataset:
    frame: pd.DataFrame
    sha256: str
    dvc_metadata: str | None


def validate_features(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(FEATURES) - set(frame.columns))
    if missing:
        raise ValueError(f"Kolom fitur tidak lengkap: {missing}")
    if frame.empty:
        raise ValueError("Dataset tidak boleh kosong.")
    features = frame.loc[:, FEATURES]
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in features.dtypes):
        raise ValueError("Semua fitur harus berupa angka.")
    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError("Fitur berisi nilai kosong, NaN, atau infinity.")
    return features


def load_dataset(path: str | Path, *, require_dvc: bool = True) -> Dataset:
    path = Path(path)
    content = path.read_bytes()
    frame = pd.read_csv(BytesIO(content))
    validate_features(frame)
    if TARGET not in frame or not pd.api.types.is_numeric_dtype(frame[TARGET]):
        raise ValueError(f"Dataset harus mempunyai target numerik {TARGET}.")
    if not np.isfinite(frame[TARGET].to_numpy(dtype=float)).all():
        raise ValueError("Target berisi nilai kosong, NaN, atau infinity.")
    metadata_path = path.with_suffix(path.suffix + ".dvc")
    metadata = None
    if metadata_path.exists():
        metadata = metadata_path.read_text(encoding="utf-8")
        outputs = yaml.safe_load(metadata).get("outs", [])
        matching = [out for out in outputs if out.get("path") == path.name]
        if len(matching) != 1 or "md5" not in matching[0]:
            raise ValueError("Metadata DVC harus mencatat satu CSV dengan hash MD5.")
        actual = hashlib.md5(content, usedforsecurity=False).hexdigest()
        if matching[0]["md5"] != actual:
            raise ValueError("CSV berbeda dari versi DVC. Jalankan dvc add sebelum training.")
    elif require_dvc:
        raise FileNotFoundError(f"Metadata belum ada: {metadata_path}. Jalankan dvc add.")
    return Dataset(frame, hashlib.sha256(content).hexdigest(), metadata)


def prepare_data(path: str | Path, *, from_source: bool = False) -> Path:
    path = Path(path)
    if path.exists():
        return path
    metadata_path = path.with_suffix(path.suffix + ".dvc")
    if metadata_path.exists() and not from_source:
        raise FileNotFoundError(
            "CSV belum tersedia tetapi metadata DVC ada. "
            "Jalankan dvc checkout atau dvc pull agar versi data tetap sesuai. "
            "Untuk dataset awal publik, gunakan prepare-data --from-source."
        )
    housing = fetch_california_housing(as_frame=True)
    content = housing.frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    if metadata_path.exists():
        outputs = yaml.safe_load(metadata_path.read_text(encoding="utf-8")).get("outs", [])
        matches = [out for out in outputs if out.get("path") == path.name]
        if len(matches) != 1 or "md5" not in matches[0]:
            raise ValueError("Metadata DVC tidak memiliki hash dataset yang valid.")
        # The first notebook snapshot may have used Windows CRLF line endings.
        candidates = [content, housing.frame.to_csv(index=False, lineterminator="\r\n").encode()]
        content = next(
            (
                candidate
                for candidate in candidates
                if hashlib.md5(candidate, usedforsecurity=False).hexdigest() == matches[0]["md5"]
            ),
            None,
        )
        if content is None:
            raise ValueError(
                "Dataset sumber tidak cocok dengan versi DVC ini. "
                "Pulihkan versi yang benar dari cache/remote; file tidak dibuat."
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path
