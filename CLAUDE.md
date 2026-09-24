# Charging dock (build123d)

Parametric 3D-print models for a cycling-electronics charging dock: a tapered base, a tray with fixed dividers, and a hinged lid, plus clearance and hinge calibration coupons. Spec and plan live in docs/superpowers/; the current design is specs/2026-09-23-tapered-dock-design.md. The printed v1 prototype is tagged `v1-prototype`.

## Toolchain
- Python 3.12 via uv only (system Python is 3.14; build123d has no wheels for it): `uv venv --python 3.12 && uv pip install -e ".[dev]"`, then `uv run pytest` / `uv run python scripts/export_all.py`.
- Slice in Snapmaker Orca (Flatpak io.github.Snapmaker.Snapmaker_Orca) for the Snapmaker U1, PETG. See docs/printing.md.
- `uv run python scripts/slice_report.py [--layer 0.28]` slices out/base,tray,lid headlessly and compares time and grams with v1 (not part of pytest; minutes). The design target is at least 25 % below v1 in both.
- `uv run python scripts/orca_project.py` builds out/orca/dock_plates.3mf, every part on its own named Orca plate (the Orca CLI's own assemble-list and 3mf loading segfault in this Flatpak, so it arranges STLs and rewrites the plates).
- build123d 0.12: `part.is_valid` is a property; `ShapeList.sort_by(Axis.Z)`, not a lambda.

## Conventions
- All dimensions in mm; design rules in src/dock/params.py, caliper inputs in src/dock/measurements.py (values marked NOMINAL are guesses until measured; see docs/measuring.md).
- Every outer face shares one 15 degree draft: build drafted shapes from `taper.Outline` (layout.RIM, layout.TRAY_OUTLINE), never by hand, so corners stay concentric. Where things go is in layout.py (numbers only).
- One `build_*()` per printed part, print-bed face at Z=0, algebra API (`Box - Pos(...) * Box`). XY is centred and shared by every part.
- Tests must measure the built solid (faces, wires, bounding boxes, intersections, probes), not restate constants. Every exported part is checked as a single valid solid on the bed in tests/test_parts.py; overhangs through tests/printability.py.
- Chamfers not fillets on downward edges; no overhang past 45 degrees; short bridges (<= 20 mm) are allowlisted in the overhang tests.
- out/ is gitignored; never commit exports.
