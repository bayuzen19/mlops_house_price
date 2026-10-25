"""Package only classroom source files; omit data, outputs, secrets, and caches."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "house_price_project.zip"
FILES = [
    ".dockerignore",
    ".dvc/.gitignore",
    ".dvc/config",
    ".dvcignore",
    ".gitattributes",
    ".gitignore",
    "Dockerfile",
    "README.md",
    "MULAI_DARI_ZIP.md",
    "dvc.yaml",
    "params.yaml",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "data/raw/.gitignore",
    "data/raw/california_housing.csv.dvc",
    "scripts/check_notebook.py",
    "scripts/smoke_test.py",
    "scripts/package_project.py",
]
PATTERNS = {
    "src/house_price": "*.py",
    "tests": "*.py",
    "configs": "*.yaml",
    "notebooks": "*.ipynb",
    ".github/workflows": "*.yml",
}


def package():
    selected = [ROOT / item for item in FILES]
    for folder, pattern in PATTERNS.items():
        selected.extend(sorted((ROOT / folder).glob(pattern)))
    for path in selected:
        if not path.is_file():
            raise FileNotFoundError(path)
    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in selected:
            name = "house_price/" + path.relative_to(ROOT).as_posix()
            if path.suffix == ".ipynb":
                # Strip execution outputs in the ZIP only; preserve notebooks on disk.
                notebook = json.loads(path.read_text(encoding="utf-8"))
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        cell["execution_count"] = None
                        cell["outputs"] = []
                archive.writestr(name, json.dumps(notebook, indent=1, ensure_ascii=False) + "\n")
            else:
                archive.write(path, name)
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist())) == len(selected)
    checksum = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix(".zip.sha256").write_text(f"{checksum}  {OUTPUT.name}\n", encoding="utf-8")
    print(f"{OUTPUT}: {len(selected)} files, {OUTPUT.stat().st_size:,} bytes")
    print(f"SHA-256: {checksum}")


if __name__ == "__main__":
    package()
