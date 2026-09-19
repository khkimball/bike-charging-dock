# Charging dock

Parametric build123d model of a desktop charging dock. See
`docs/superpowers/specs/2026-09-19-charging-dock-design.md`.

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    uv run pytest
    uv run python scripts/export_all.py     # writes out/*.stl|3mf|step
    uv run python -m ocp_vscode             # viewer at http://localhost:3939
