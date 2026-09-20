# Charging dock

Parametric build123d model of a desktop charging dock. See
`docs/superpowers/specs/2026-09-20-tray-dock-design.md`.

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    uv run pytest
    uv run python scripts/export_all.py     # writes out/*.stl|step
    uv run python -m ocp_vscode             # viewer at http://localhost:3939

## Parts

- **coupon** -- calibration plate and peg, printed first to set the fit
  clearances against the real printer.
- **tray** -- flat plate with four device bays (Roam, Ion, Trackr, and a
  spare) and two removable **dividers** between the right-hand bays.
- **base** -- the lower box: hides the charger and cable slack, and the
  tray drops into a rebate in its top rim.
- **lid** -- a shallow lift-off cap that drops over the outside of the base.

## Workflow

1. Measure the hardware and cables per `docs/measuring.md`, filling in
   `src/dock/measurements.py` and `src/dock/params.py`.
2. Run `uv run pytest` and `uv run python scripts/export_all.py`.
3. Print and fit-check following `docs/printing.md` (coupon first, then the
   tray and dividers, the base, and the lid), looping back to step 1 as
   clearances need adjusting.
