"""Read the same training parameters from the CLI and the notebook."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class TrainingConfig:
    test_size: float = 0.3
    random_state: int = 42
    cv: int = 3
    n_jobs: int = -1
    param_grid: dict = field(
        default_factory=lambda: {
            "n_estimators": [100, 200],
            "max_depth": [5, 10, None],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
        }
    )
    experiment_name: str = "house-price"
    registered_model_name: str | None = "Best Random Forest Model"

    def __post_init__(self):
        if not 0 < self.test_size < 1:
            raise ValueError("test_size harus berada di antara 0 dan 1.")
        if self.cv < 2 or self.n_jobs == 0:
            raise ValueError("cv minimal 2 dan n_jobs tidak boleh 0.")
        allowed = {"n_estimators", "max_depth", "min_samples_split", "min_samples_leaf"}
        if not self.param_grid or set(self.param_grid) - allowed:
            raise ValueError(f"Parameter grid yang didukung: {sorted(allowed)}")
        if any(not isinstance(values, list) or not values for values in self.param_grid.values()):
            raise ValueError("Setiap parameter grid harus berisi list yang tidak kosong.")


def load_config(path: str | Path) -> TrainingConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) - {"training", "mlflow"}:
        raise ValueError("Konfigurasi hanya mendukung bagian training dan mlflow.")
    return TrainingConfig(**raw.get("training", {}), **raw.get("mlflow", {}))
