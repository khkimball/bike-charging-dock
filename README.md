# Charging dock

Parametric build123d model of a desktop charging dock: a tapered, hinged,
two-tone design. See
`docs/superpowers/specs/2026-09-23-tapered-dock-design.md`.

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    uv run pytest
    uv run python scripts/export_all.py     # writes out/*.stl|step
    uv run python -m ocp_vscode             # viewer at http://localhost:3939

## Parts

- **coupon** -- calibration plate and peg, and a hinge coupon (one hinge
  station on a short stretch of wall and lid), printed first to set the fit
  clearances and the hinge's snap fit against the real printer.
- **tray** -- flat plate with four device bays (Roam, Ion, Trackr, and a
  spare) and fixed dividers between the right-hand bays, fused to the plate
  and outer walls.
- **base** -- the tapered, two-tone lower shell: hides the charger and cable
  slack, and carries the tray on a ledge at its inner wall.
- **lid** -- a tapered, hinged cap that snaps onto pins on the base and
  swings open; no hardware.

## Workflow

1. Measure the hardware and cables per `docs/measuring.md`, filling in
   `src/dock/measurements.py` and `src/dock/params.py`.
2. Run `uv run pytest` and `uv run python scripts/export_all.py`.
3. Print and fit-check following `docs/printing.md` (the coupon and hinge
   coupon first, then the tray, the base, and the lid), looping back to
   step 1 as clearances need adjusting.
