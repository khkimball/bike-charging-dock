"""Run `uv run python -m ocp_vscode` in one terminal, then call show_part()."""
from build123d import Part
from ocp_vscode import show


def show_part(part: Part) -> None:
    show(part)
