"""Validate notebook structure and Python syntax without launching full training."""

import ast
from pathlib import Path

import nbformat

paths = sorted((Path(__file__).resolve().parents[1] / "notebooks").glob("*.ipynb"))
if not paths:
    raise SystemExit("No notebooks found")
for path in paths:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            ast.parse(cell.source, filename=f"{path.name}:cell-{index}")
    print(f"{path.name}: structure and code syntax OK")
