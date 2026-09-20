# Charging dock (build123d)

Parametric 3D-print models for a cycling-electronics charging dock: tray, base, lid, and removable dividers, plus a coupon calibration part. Spec and plan live in docs/superpowers/.

## Toolchain
- Python 3.12 via uv only (system Python is 3.14; build123d has no wheels for it): `uv venv --python 3.12 && uv pip install -e ".[dev]"`, then `uv run pytest` / `uv run python scripts/export_all.py`.
- Slice in Snapmaker Orca (Flatpak io.github.Snapmaker.Snapmaker_Orca) for the Snapmaker U1, PETG. See docs/printing.md.
- build123d 0.12: `part.is_valid` is a property; `ShapeList.sort_by(Axis.Z)`, not a lambda.

## Conventions
- All dimensions in mm; design rules in src/dock/params.py, caliper inputs in src/dock/measurements.py (values marked NOMINAL are guesses until measured; see docs/measuring.md).
- One `build_*()` per printed part, print-bed face at Z=0, algebra API (`Box - Pos(...) * Box`).
- Tests must measure the built solid (faces, wires, bounding boxes, intersections), not restate constants. Every exported part is checked as a single valid solid on the bed in tests/test_parts.py.
- Chamfers not fillets on downward edges; no overhang past 45 degrees; short bridges (<= 20 mm) are allowlisted in the overhang tests.
- out/ is gitignored; never commit exports.
