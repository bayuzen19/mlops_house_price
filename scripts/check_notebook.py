"""Validate notebook structure and Python syntax without launching full training."""

import ast
from pathlib import Path

import nbformat

path = Path(__file__).resolve().parents[1] / "notebooks" / "experiments.ipynb"
notebook = nbformat.read(path, as_version=4)
nbformat.validate(notebook)
for index, cell in enumerate(notebook.cells):
    if cell.cell_type == "code":
        ast.parse(cell.source, filename=f"{path.name}:cell-{index}")
print("Notebook structure and code syntax: OK")
