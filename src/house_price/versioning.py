"""Small DVC helpers shared by the notebook and CLI."""

import subprocess
import sys
from pathlib import Path


def run_dvc(project_root: str | Path, *args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "dvc", *args],
        cwd=project_root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def track_data(project_root: str | Path, data_path: str | Path) -> str:
    root = Path(project_root).resolve()
    path = Path(data_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Dataset harus berada di dalam folder proyek DVC.")
    return run_dvc(root, "add", path.relative_to(root).as_posix())
