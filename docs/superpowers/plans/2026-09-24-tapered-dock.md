# Tapered Dock (physical v2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v1 box dock with the tapered, hinged, two-tone dock of the spec, at least 25 % cheaper to print than v1 in both time and filament.

**Architecture:** Two new number/geometry helpers carry the shared shape: `taper.py` (the 15° drafted rounded outline) and `layout.py` (bay rectangles, outlines, heights, as numbers). `hinge.py` builds both halves of the snap-on hinge in base coordinates. `tray.py`, `base.py` and `lid.py` are rewritten on top of those, one per task, each replacing its v1 module and v1 tests; the removable divider goes. Every code block below was built and its tests run green in a scratch worktree during planning (95 tests at the end state).

**Tech Stack:** Python 3.12, build123d 0.12 (algebra API), pytest, uv; Snapmaker Orca Flatpak for slicing.

**Spec:** docs/superpowers/specs/2026-09-23-tapered-dock-design.md

## Global Constraints

- Python 3.12 through uv only: `uv run pytest`, `uv run python scripts/...`. Never system Python.
- All dimensions in mm. Design rules in `src/dock/params.py`; caliper inputs in `src/dock/measurements.py`; never inline a number that belongs there.
- One `build_*()` per printed part; each part's bed face at Z = 0; XY centred and shared by all parts.
- Tests measure the built solid (faces, bounding boxes, intersections, probes), never restate a constant.
- Every downward face ≤ 45° off vertical, except allowlisted bridges ≤ 20 mm and the one supported ceiling (the cord port). Chamfers, not fillets, on downward edges.
- `out/` is gitignored; never commit exports.
- Work on branch `tapered-dock`. Commit after every task, with the trailer line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- After every task, `uv run pytest` is fully green.
- Design values (spec): TAPER_DEG 15, CORNER_R 30 (rim), BAND_H 8, WALL 2.0, THIN_WALL 1.6, FLOOR 1.2, TRAY_PLATE 1.2, LID_PLATE 1.2, CLR_BAY 8, CLR_BAY_OUTER 3, BAY_DEPTH 38, BED 250 × 250.

## File structure

| File | Status | Responsibility |
|---|---|---|
| `scripts/slice_report.py` | new | Headless Orca slice of out/*.stl, time and grams vs the v1 baseline |
| `src/dock/params.py` | modify | v2 design rules (temporary `V1_*` shims until Task 6) |
| `src/dock/measurements.py` | modify | `Charger.corner_r` |
| `src/dock/taper.py` | new | 15° draft, `Outline`, `corner_rect`, `horiz`, `bed_chamfer_inset` |
| `src/dock/layout.py` | new | Bays, device footprints, cutouts, heights, tray/rim outlines, lid lip |
| `src/dock/hinge.py` | new | Axis, pins/cheeks, hooks, heel, relief discs, `opened()` |
| `src/dock/coupon.py` | modify | + `build_hinge_coupon()` |
| `src/dock/lid.py` | rewrite | Tapered hinged lid, `build_lid()`, `lid_seat(deg)` |
| `src/dock/base.py` | rewrite | Tapered two-tone base, ledge, fence, ports, hinge pins, `tray_seat()` |
| `src/dock/tray.py` | rewrite | Tapered tray, fixed filleted dividers, finger slot |
| `src/dock/divider.py` | delete | (dividers are now fixed) |
| `scripts/export_all.py` | modify | PARTS and a bounding-box build report |
| `tests/printability.py` | new | `steep_faces`, `span`, `overhang_deg` helpers |
| `tests/test_taper.py`, `test_layout.py`, `test_hinge.py` | new | |
| `tests/test_lid.py`, `test_base.py`, `test_tray.py`, `test_assembly.py` | rewrite | |
| `tests/test_divider.py` | delete | |
| `tests/test_params.py`, `test_measurements.py`, `test_coupon.py` | modify | |
| `docs/printing.md`, `docs/measuring.md`, `CLAUDE.md` | modify | |

Test files import sibling helpers (`from printability import ...`); pytest's default rootdir-prepend import mode puts `tests/` on the path, so no `__init__.py` or conftest is needed.

---

### Task 1: Slice report

**Files:**
- Create: `scripts/slice_report.py`

**Interfaces:**
- Produces: `uv run python scripts/slice_report.py [--layer 0.20|0.28] [STL ...]` → prints a part | time | grams table, a total, and (with no STL arguments) the v2-set-vs-v1-set percentages. Writes only under `out/slice/`.

Not TDD: it drives the Flatpak and takes minutes, so it is verified by reproducing the v1 baseline.

- [ ] **Step 1: Write the script**

```python
"""Slice the exported parts headlessly in Snapmaker Orca and report print
time and filament for each, next to the v1 baseline.

    uv run python scripts/slice_report.py                  # 0.20 Standard, the dock set in out/
    uv run python scripts/slice_report.py --layer 0.28     # 0.28 Extra Draft
    uv run python scripts/slice_report.py releases/v1-prototype/tray.stl

It needs the Snapmaker Orca Flatpak and takes minutes, so it is not part of
pytest.  The profiles are the vendor's own -- Snapmaker U1 (0.4 nozzle), the
0.20 Standard or 0.28 Extra Draft process, Generic PETG -- flattened at run
time, with the per-part settings from docs/printing.md laid over them: three
walls and 15 % infill everywhere, supports only for the base.

The Orca CLI in this Flatpak has three quirks, each handled below:
- system profiles `inherits` from one another and the CLI will not follow
  the chain, so each is flattened into one standalone JSON first -- keeping
  `"from": "system"`, because a flattened "User" process is then reported as
  incompatible with the printer (return code -17);
- any process carrying the key `wipe_tower_filament` segfaults it (exit 139),
  so that key is dropped;
- `--export-3mf` is joined onto `--outputdir`, so it gets a bare file name.
The estimates are read from the gcode header inside the exported 3mf.
"""
import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

APP = "io.github.Snapmaker.Snapmaker_Orca"
MACHINE = "Snapmaker U1 (0.4 nozzle)"
PROCESS = {"0.20": "0.20 Standard @Snapmaker U1 (0.4 nozzle)",
           "0.28": "0.28 Extra Draft @Snapmaker U1 (0.4 nozzle)"}
FILAMENT = "Generic PETG"
SUPPORTED = {"base"}             # parts that print with supports
DOCK_SET = ("base", "tray", "lid")
# The v1 prototype's STLs (releases/v1-prototype/) through this same script
# at 0.20, 2026-09-24: (minutes, grams) per part, and how many of each part a
# v1 set needed.  Re-run it on those STLs if the Flatpak's profiles change.
BASELINE = {"base": (355, 263.7), "tray": (262, 184.5), "lid": (135, 103.8),
            "divider": (44, 15.2)}
BASELINE_COUNT = {"base": 1, "tray": 1, "lid": 1, "divider": 2}
OUT = Path("out/slice")


def _profiles_root() -> Path:
    loc = subprocess.run(["flatpak", "info", "--show-location", APP],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(loc) / "files/share/Snapmaker_Orca/profiles"


def _index(root: Path, kind: str) -> dict[str, Path]:
    """name -> file for every `kind` (machine/process/filament) profile."""
    idx: dict[str, Path] = {}
    for fp in root.rglob(f"{kind}/*.json"):
        try:
            name = json.loads(fp.read_text()).get("name")
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if name and name not in idx:
            idx[name] = fp
    return idx


def _flatten(idx: dict[str, Path], name: str) -> dict:
    d = json.loads(idx[name].read_text())
    parent = d.pop("inherits", None)
    merged = _flatten(idx, parent) if parent else {}
    merged.update(d)
    merged["from"] = "system"
    merged.pop("inherits", None)
    return merged


def _write(d: dict, path: Path) -> Path:
    path.write_text(json.dumps(d, indent=4))
    return path.resolve()


def _minutes(text: str) -> float:
    total = 0.0
    for n, unit in re.findall(r"(\d+)([dhms])", text):
        total += int(n) * {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}[unit]
    return total


def _estimates(threemf: Path) -> tuple[float, float]:
    with zipfile.ZipFile(threemf) as z:
        gcode = next(n for n in z.namelist() if n.endswith(".gcode"))
        head = z.read(gcode).decode(errors="replace")
    t = re.search(r"estimated printing time \(normal mode\) = ([^\n]+)", head)
    g = re.search(r"total filament used \[g\] = ([\d.]+)", head)
    if not (t and g):
        raise RuntimeError(f"no estimates in {threemf}")
    return _minutes(t.group(1)), float(g.group(1))


def slice_part(stl: Path, layer: str, prof: dict[str, Path]) -> tuple[float, float]:
    name = stl.stem
    outdir = (OUT / f"{name}_{layer}").resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    process = prof["support" if name in SUPPORTED else "plain"]
    cmd = ["flatpak", "run", f"--filesystem={OUT.resolve()}",
           f"--filesystem={stl.resolve().parent}", APP,
           "--load-settings", f"{prof['machine']};{process}",
           "--load-filaments", str(prof["filament"]),
           "--slice", "0", "--export-3mf", f"{name}.3mf",
           "--outputdir", str(outdir), str(stl.resolve())]
    run = subprocess.run(cmd, capture_output=True, text=True)
    result = outdir / "result.json"
    rc = json.loads(result.read_text()).get("return_code") if result.exists() else None
    if run.returncode != 0 or rc not in (0, None):
        raise RuntimeError(f"{name}: orca exit {run.returncode}, return_code {rc}\n"
                           f"{run.stderr[-2000:]}")
    return _estimates(outdir / f"{name}.3mf")


def _fmt(minutes: float) -> str:
    return f"{int(minutes // 60)}h{int(round(minutes % 60)):02d}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stls", nargs="*", type=Path)
    ap.add_argument("--layer", choices=sorted(PROCESS), default="0.20")
    args = ap.parse_args()
    stls = args.stls or [Path("out") / f"{n}.stl" for n in DOCK_SET]
    missing = [s for s in stls if not s.exists()]
    if missing:
        print(f"missing: {', '.join(map(str, missing))} -- run scripts/export_all.py",
              file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    root = _profiles_root()
    proc = _flatten(_index(root, "process"), PROCESS[args.layer])
    proc.pop("wipe_tower_filament", None)
    proc.update({"wall_loops": "3", "sparse_infill_density": "15%"})
    prof = {
        "machine": _write(_flatten(_index(root, "machine"), MACHINE), OUT / "machine.json"),
        "filament": _write(_flatten(_index(root, "filament"), FILAMENT), OUT / "filament.json"),
        "plain": _write({**proc, "enable_support": "0"}, OUT / f"process_{args.layer}.json"),
        "support": _write({**proc, "enable_support": "1"}, OUT / f"process_{args.layer}_s.json"),
    }

    total_t = total_g = 0.0
    print(f"slice report: {PROCESS[args.layer]}, {FILAMENT}")
    print(f"  {'part':<10}{'time':>8}{'grams':>9}   v1 time   v1 g")
    for stl in stls:
        t, g = slice_part(stl, args.layer, prof)
        total_t, total_g = total_t + t, total_g + g
        base = BASELINE.get(stl.stem)
        ref = f"   {_fmt(base[0]):>7}{base[1]:7.1f}" if base else ""
        print(f"  {stl.stem:<10}{_fmt(t):>8}{g:9.1f}{ref}")
    v1_t = sum(BASELINE[n][0] * c for n, c in BASELINE_COUNT.items())
    v1_g = sum(BASELINE[n][1] * c for n, c in BASELINE_COUNT.items())
    print(f"  {'total':<10}{_fmt(total_t):>8}{total_g:9.1f}   {_fmt(v1_t):>7}{v1_g:7.1f}")
    if not args.stls:
        print(f"  v2 set vs v1 set: time {100 * (total_t / v1_t - 1):+.0f} %, "
              f"filament {100 * (total_g / v1_g - 1):+.0f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Reproduce the v1 baseline**

Run: `uv run python scripts/slice_report.py releases/v1-prototype/tray.stl releases/v1-prototype/lid.stl releases/v1-prototype/base.stl releases/v1-prototype/divider.stl`
Expected (±1 %): tray 4h22 184.5 g, lid 2h15 103.8 g, base 5h55 263.7 g, divider 0h44 15.2 g. If the Flatpak's profiles changed and these moved, update `BASELINE` from this run and say so in the commit message.

- [ ] **Step 3: Commit**

```bash
git add scripts/slice_report.py
git commit -m "Slice report: headless Orca time and grams against the v1 baseline"
```

---

### Task 2: Design rules, charger corner, taper and layout

**Files:**
- Modify: `src/dock/params.py`, `src/dock/measurements.py`, `docs/measuring.md`
- Modify (mechanical rename only): `src/dock/base.py`, `src/dock/tray.py`, `src/dock/lid.py`, `src/dock/divider.py`, `tests/test_base.py`, `tests/test_tray.py`, `tests/test_lid.py`, `tests/test_assembly.py`, `tests/test_divider.py`
- Create: `src/dock/taper.py`, `src/dock/layout.py`, `tests/test_taper.py`, `tests/test_layout.py`
- Test: `tests/test_params.py`, `tests/test_measurements.py`

**Interfaces:**
- Produces: `params` v2 names (above); `measurements.Charger.corner_r` (float, default 6.0); `taper.TAN`, `taper.COS`, `taper.horiz(t)`, `taper.bed_chamfer_inset()`, `taper.Outline(sx, sy, r, z_ref)` with `.at(z, inset=0) -> (sx, sy, r)`, `.section(z, inset=0) -> Sketch`, `.solid(z0, z1, inset=0) -> Part`; `taper.corner_rect(x0, x1, y0, y1, radii: dict[str, float], z) -> Sketch` (keys "--", "+-", "++", "-+"); `layout.Bay` (name, x0, x1, y0, y1, sloped: (−X, +X, −Y, +Y), .cx, .cy), `layout.BAYS` (roam, spare, trackr, ion), `layout.DEVICES`, `layout.device_footprint(name) -> (x0, x1, y0, y1)`, `layout.cutouts() -> [(bay, cx, cy, sx, sy)]`, `layout.TRAY_H`, `BASE_H`, `TRAY_Z0`, `TRAY_OUTLINE`, `RIM`, `LIP_W`, `LID_H`, `LID_SLOPE_H`, `LIP_H`, `TRAY_SINK`, `TRAY_GAP`, `INNER_FILLET_R`, `FLOOR_FILLET_R`, `CUTOUT`, `CUTOUT_INSET`, `UNDERSIDE_PORT_CUTOUTS`, `FLOOR_X`, `FLOOR_Y`.

The v1 modules still use `WALL`, `FLOOR`, `CORNER_R` and `TRAY_PLATE`, whose values change here. To keep v1 building (and its tests green) until each module is replaced, they are renamed to `V1_*` copies holding the old values.

- [ ] **Step 1: Write the failing tests**

`tests/test_taper.py`:

```python
import math

from build123d import Axis, GeomType

from dock import params, taper


def _circle_radii(face):
    return sorted({round(e.radius, 3) for e in face.edges()
                   if e.geom_type == GeomType.CIRCLE})


def test_the_draft_is_the_spec_angle():
    assert math.isclose(math.degrees(math.atan(taper.TAN)), params.TAPER_DEG)


def test_a_drafted_solid_leans_by_the_draft_on_every_side():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    p = o.solid(10.0, 50.0)
    faces = p.faces().sort_by(Axis.Z)
    bottom, top = faces[0].bounding_box().size, faces[-1].bounding_box().size
    lean = 40.0 * math.tan(math.radians(params.TAPER_DEG))
    assert math.isclose(top.X - bottom.X, 2 * lean, abs_tol=1e-4)
    assert math.isclose(top.Y - bottom.Y, 2 * lean, abs_tol=1e-4)


def test_the_corner_radius_shrinks_with_the_draft_so_corners_stay_concentric():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    p = o.solid(10.0, 50.0)
    faces = p.faces().sort_by(Axis.Z)
    lean = 40.0 * taper.TAN
    assert _circle_radii(faces[-1]) == [20.0]
    assert _circle_radii(faces[0]) == [round(20.0 - lean, 3)]


def test_an_inset_outline_is_a_wall_thickness_in_from_it():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    outer = o.solid(0.0, 50.0).faces().sort_by(Axis.Z)[-1].bounding_box().size
    inner = o.solid(0.0, 50.0, inset=taper.horiz(2.0)).faces().sort_by(Axis.Z)[-1].bounding_box().size
    # measured square to the drafted face, the wall is 2.0 thick
    assert math.isclose((outer.X - inner.X) / 2 * taper.COS, 2.0, abs_tol=1e-4)


def test_above_its_reference_height_an_outline_grows():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=0.0)
    sx, sy, r = o.at(10.0)
    assert sx > 100.0 and sy > 60.0 and r > 20.0


def test_corner_rect_rounds_each_corner_by_its_own_radius():
    s = taper.corner_rect(0, 40, 0, 30, {"--": 10.0, "+-": 3.0, "++": 0.0, "-+": 5.0}, z=0)
    assert _circle_radii(s.faces()[0]) == [3.0, 5.0, 10.0]


def test_bed_chamfer_inset_makes_a_45_degree_foot_on_a_drafted_wall():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    lo = o.at(0.0, taper.bed_chamfer_inset())[0]
    hi = o.at(params.CHAMFER)[0]
    assert math.isclose((hi - lo) / 2, params.CHAMFER, abs_tol=1e-9)
```

`tests/test_layout.py`:

```python
"""The layout is numbers, so these check the relations the parts rely on:
bays tile the tray floor, devices fit their bays, the stack-up adds up."""
import math

from dock import measurements as m
from dock import layout as L, params, taper


def test_the_four_bays_tile_the_tray_floor_with_wall_thick_gaps():
    b = L.BAYS
    assert math.isclose(b["spare"].x0 - b["roam"].x1, params.WALL)
    assert math.isclose(b["trackr"].y0 - b["spare"].y1, params.WALL)
    assert math.isclose(b["ion"].y0 - b["trackr"].y1, params.WALL)
    assert math.isclose(b["roam"].x0, -L.FLOOR_X / 2)
    assert math.isclose(b["spare"].x1, L.FLOOR_X / 2)
    for bay in b.values():
        assert bay.y0 >= -L.FLOOR_Y / 2 - 1e-9 and bay.y1 <= L.FLOOR_Y / 2 + 1e-9


def test_a_bay_side_is_sloped_exactly_when_it_is_on_the_floor_outline():
    for bay in L.BAYS.values():
        on_edge = (math.isclose(bay.x0, -L.FLOOR_X / 2), math.isclose(bay.x1, L.FLOOR_X / 2),
                   math.isclose(bay.y0, -L.FLOOR_Y / 2), math.isclose(bay.y1, L.FLOOR_Y / 2))
        assert bay.sloped == on_edge, bay.name


def test_each_device_sits_inside_its_bay_with_its_clearances():
    for name in L.DEVICES:
        bay = L.BAYS[name]
        x0, x1, y0, y1 = L.device_footprint(name)
        sides = (x0 - bay.x0, bay.x1 - x1, y0 - bay.y0, bay.y1 - y1)
        for gap, sloped in zip(sides, bay.sloped):
            need = params.CLR_BAY_OUTER if sloped else params.CLR_BAY
            assert gap >= need - 1e-9, (name, gap, need)


def test_cutouts_sit_in_their_bays_clear_of_the_floor_fillet_and_the_device():
    for name, cx, cy, sx, sy in L.cutouts():
        bay = L.BAYS[name]
        assert bay.x0 + L.FLOOR_FILLET_R < cx - sx / 2 and cx + sx / 2 < bay.x1 - L.FLOOR_FILLET_R
        assert bay.y0 + L.FLOOR_FILLET_R < cy - sy / 2 and cy + sy / 2 < bay.y1 - L.FLOOR_FILLET_R
        if name in L.DEVICES and name not in L.UNDERSIDE_PORT_CUTOUTS:
            x0, x1, y0, y1 = L.device_footprint(name)
            clear_x = cx + sx / 2 <= x0 or cx - sx / 2 >= x1
            clear_y = cy + sy / 2 <= y0 or cy - sy / 2 >= y1
            assert clear_x or clear_y, name


def test_six_cutouts_three_under_the_ion():
    names = [c[0] for c in L.cutouts()]
    assert len(names) == 6 and names.count("ion") == 3


def test_the_stack_up_puts_the_tray_on_the_cable_room_above_the_charger():
    assert math.isclose(L.TRAY_Z0, params.FLOOR + m.CHARGER.height + L.CABLE_ROOM)
    assert math.isclose(L.TRAY_Z0 + L.TRAY_H + L.TRAY_SINK, L.BASE_H)


def test_the_tray_and_the_rim_share_corner_centres():
    t, r = L.TRAY_OUTLINE, L.RIM
    at_rim = t.at(L.TRAY_H + L.TRAY_SINK)   # the tray outline carried up to rim height
    assert math.isclose(r.sx / 2 - r.r, at_rim[0] / 2 - at_rim[2], abs_tol=1e-9)


def test_the_tray_floor_outline_is_the_bays_plus_a_thin_wall():
    sx, sy, _ = L.TRAY_OUTLINE.at(params.TRAY_PLATE)
    assert math.isclose(sx, L.FLOOR_X + 2 * taper.horiz(params.THIN_WALL))
    assert math.isclose(sy, L.FLOOR_Y + 2 * taper.horiz(params.THIN_WALL))


def test_the_lid_lip_keeps_at_least_a_millimetre_inside_the_bed():
    assert 1.0 <= L.LIP_W <= L.LIP_W_MAX
```

Replace `test_design_rules_match_spec` in `tests/test_params.py` with:

```python
def test_design_rules_match_spec():
    assert params.WALL == 2.0
    assert params.THIN_WALL == 1.6
    assert params.FLOOR == 1.2
    assert params.CLR_FIT == 0.15
    assert params.CLR_BAY == 8.0
    assert params.CLR_BAY_OUTER == 3.0
    assert params.TRAY_PLATE == 1.2
    assert params.LID_PLATE == 1.2
    assert params.BAY_DEPTH == 38.0
    assert params.TAPER_DEG == 15.0
    assert params.CORNER_R == 30.0
    assert params.BAND_H == 8.0
    assert (params.BED_X, params.BED_Y) == (250, 250)
```

Append to `tests/test_measurements.py`:

```python
def test_the_charger_corner_radius_fits_the_body():
    c = m.CHARGER
    assert 0 < c.corner_r < min(c.port_face_width, c.port_to_inlet) / 2
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_taper.py tests/test_layout.py tests/test_params.py tests/test_measurements.py -q`
Expected: collection errors (`No module named 'dock.taper'`) and `test_design_rules_match_spec` failing on `THIN_WALL`.

- [ ] **Step 3: Write `src/dock/params.py`**

Replace the whole file with (the `V1_*` block is temporary):

```python
"""Design rules for the tapered dock. Millimetres. Change here, never inline
in a part module."""
from dataclasses import dataclass

WALL = 2.0         # base shell and tray dividers: 5 lines at 0.4 mm (v1: 2.4)
THIN_WALL = 1.6    # 2 perimeters a side: the tray's hidden outer walls, the lid's walls
FLOOR = 1.2        # base floor: 6 layers at 0.2 mm (v1: 1.6)
CHAMFER = 1.0      # downward-facing edge chamfer
CLR_FIT = 0.15     # coupon 2026-09-20, PLA on U1: 0.10 tight, 0.15 slides
CLR_BAY = 8.0      # device to a vertical (internal) bay wall; room for the cable beside it
CLR_BAY_OUTER = 3.0  # device to a sloped (outer) bay wall at the floor; the lean opens it
                     # to ~13 mm by the rim
TRAY_PLATE = 1.2   # tray floor: 6 layers; cable cutouts pass through it (v1: 3.0)
LID_PLATE = 1.2    # lid top: 6 layers
BAY_DEPTH = 38.0   # bay wall height above the tray plate (v2.1: was 32); must clear the
                   # tallest device (ION 30.2) so the lid does not touch it
TAPER_DEG = 15.0   # every outer face leans this far off vertical, like the Trek CHRGtime
CORNER_R = 30.0    # base rim corner radius; the draft shrinks it to ~R8 at the foot
BAND_H = 8.0       # colour line: dark foot band below, light body above
BED_X = 250        # U1 usable X with margin
BED_Y = 250        # U1 usable Y with margin
THRU = 400.0       # cutter length; longer than any part in this design

# v1 values, kept only until the v1 modules that use them are replaced
# (Tasks 4-6).  Task 6 deletes these three lines.
V1_WALL = 2.4
V1_FLOOR = 1.6
V1_CORNER_R = 8.0
V1_TRAY_PLATE = 3.0
CLR_RAIL = 0.20    # one step above CLR_FIT so the divider drops in by hand


@dataclass(frozen=True)
class Plug:
    """Cable connector overmold envelope (the moulded body, not the metal tip)."""
    width: float
    height: float
    length: float   # overmold length along the cable axis


# Typical overmold sizes; refine from the actual cables when measured.  The
# tray's cable cutouts are one size for all of them (see tray.CUTOUT), so
# these are sanity limits, not cutter inputs.
USB_A_PLUG = Plug(width=15.0, height=8.0, length=20.0)
USB_C_PLUG = Plug(width=11.0, height=6.0, length=18.0)
MICRO_PLUG = Plug(width=10.5, height=6.5, length=17.0)
```

- [ ] **Step 4: Point the v1 modules and tests at the `V1_*` copies**

```bash
sed -i -E 's/\b(P|params)\.(WALL|FLOOR|CORNER_R|TRAY_PLATE)\b/\1.V1_\2/g' \
  src/dock/base.py src/dock/tray.py src/dock/lid.py src/dock/divider.py \
  tests/test_base.py tests/test_tray.py tests/test_lid.py tests/test_assembly.py tests/test_divider.py
```

Then check nothing else in those files reads the changed names: `grep -nE "\b(P|params)\.(WALL|FLOOR|CORNER_R|TRAY_PLATE)\b" src/dock/{base,tray,lid,divider}.py tests/test_{base,tray,lid,assembly,divider}.py` prints nothing.

- [ ] **Step 5: Add `corner_r` to the charger**

In `src/dock/measurements.py`, add the field as the last field of `Charger`, after `led_offset_from_ports`:

```python
    # Radius of the body's rounded vertical edges, seen from above: the
    # charger pocket's corners follow it.  See docs/measuring.md.
    corner_r: float = 6.0
```

and in the `CHARGER = Charger(...)` call replace `led_offset_from_ports=None)   # the A2154 has no LED` with:

```python
                  led_offset_from_ports=None,   # the A2154 has no LED
                  corner_r=6.0)                 # NOMINAL until measured
```

In `docs/measuring.md`, in the `CHARGER` section, add after the `led_offset_from_ports` bullet:

```markdown
- corner_r: the radius of the body's rounded vertical edges, seen from
  above.  Hold a square (or a card) against one corner, flat on both faces
  that meet there, and measure how far back along one face the curve starts
  -- that distance is the radius.  The base's charger pocket rounds its
  port-face corners to `corner_r + CLR_FIT` so they follow the body.  NOMINAL
  6.0 until measured.
```

- [ ] **Step 6: Write `src/dock/taper.py`**

```python
"""The draft every outer face of the dock shares, and the rounded outlines
it is built from.

The Trek CHRGtime's walls lean about 15 degrees off vertical (measured off
its manual's to-scale front view), and so do this dock's -- base, lid and
the tray inside, one continuous slope from the lid top to the foot.  It is a
true draft: an Outline carried down by d mm steps in d*TAN on every side and
its corner radius shrinks by the same, so everything derived from one
Outline stays concentric with it, corners included.  That is what keeps a
wall a constant thickness through its corners, and the gap between the tray
and the base uniform all the way round.
"""
import math
from dataclasses import dataclass

from build123d import Part, Plane, Pos, Rectangle, RectangleRounded, Sketch, Vector, fillet, loft

from dock import params as P

TAN = math.tan(math.radians(P.TAPER_DEG))
COS = math.cos(math.radians(P.TAPER_DEG))


def horiz(t: float) -> float:
    """Horizontal width of a wall `t` thick measured square to a drafted face."""
    return t / COS


def bed_chamfer_inset() -> float:
    """Extra inset at the bed that makes a drafted wall's foot chamfer 45
    degrees: the draft already steps the outline in CHAMFER*TAN over it."""
    return P.CHAMFER * (1 - TAN)


@dataclass(frozen=True)
class Outline:
    """A rounded rectangle centred on the Z axis: `sx` by `sy`, corner radius
    `r`, at height `z_ref`.  Carried up or down the draft it grows or shrinks
    by TAN per mm on every side, radius included."""
    sx: float
    sy: float
    r: float
    z_ref: float

    def at(self, z: float, inset: float = 0.0) -> tuple[float, float, float]:
        """(sx, sy, r) at height z, then moved `inset` further in (negative: out)."""
        i = inset + (self.z_ref - z) * TAN
        return self.sx - 2 * i, self.sy - 2 * i, self.r - i

    def section(self, z: float, inset: float = 0.0) -> Sketch:
        sx, sy, r = self.at(z, inset)
        if r <= 0:
            raise ValueError(f"corner radius {r:.2f} at z={z:.2f}: the draft ran it out")
        return Plane.XY.offset(z) * RectangleRounded(sx, sy, r)

    def solid(self, z0: float, z1: float, inset: float = 0.0) -> Part:
        """The drafted solid between z0 and z1, `inset` in from this outline."""
        return loft([self.section(z0, inset), self.section(z1, inset)])


_CORNERS = {"--": (0, 2), "+-": (1, 2), "++": (1, 3), "-+": (0, 3)}


def corner_rect(x0: float, x1: float, y0: float, y1: float,
                radii: dict[str, float], z: float) -> Sketch:
    """Rectangle x0..x1 by y0..y1 at height z, each corner rounded by its own
    radius.  Keys "--", "+-", "++", "-+" name a corner by the signs of its X
    and Y; a missing key or a radius of 0 leaves that corner square."""
    s = Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)
    xy = (x0, x1, y0, y1)
    for key, r in radii.items():
        if r <= 0:
            continue
        ix, iy = _CORNERS[key]
        s = fillet(s.vertices().sort_by_distance(Vector(xy[ix], xy[iy], 0))[0], r)
    return Plane.XY.offset(z) * s
```

- [ ] **Step 7: Write `src/dock/layout.py`**

```python
"""Where everything goes, as numbers: the tray's four bays, the outlines of
the tray, the base rim and the lid lip, and the heights they stack to.  No
solids here -- tray.py, base.py, lid.py and hinge.py build from these, and
the tests read them to know where to probe.

Coordinates: X and Y are shared by every part and centred on the dock.  Z is
each part's own: the tray's starts at its plate underside, the base's (and
the closed lid's, which is modelled sitting on the base) at the bed.

The bays are sized at the tray floor, and everything grows from there: the
tray's outer walls lean out at the draft from the floor up to its rim, the
base rim wraps that with TRAY_GAP and a WALL, and the lid continues the
slope above the rim.  Bay sides on the tray's outer wall are "sloped": a
device needs only CLR_BAY_OUTER there at the floor, because the lean opens
the gap to about 13 mm by the rim, which is where a cable runs.  Sides on an
internal wall stand vertical and keep v1's CLR_BAY.
"""
from dataclasses import dataclass

from dock import measurements as m
from dock import params as P
from dock import taper

CABLE_ROOM = 6.0          # headroom over the charger, under the tray
CUTOUT = (28.0, 16.0)     # cable cutout: (along the bay, across it), as v1
CUTOUT_INSET = 3.5        # cutout to the bay's end, clear of the R3 floor fillet
CUTOUT_GAP = 6.0          # cutout to the device, as v1
# The Ion Pro RT charges through a socket on its underside, so its bay has
# cutouts spread along it instead of one at the end.
UNDERSIDE_PORT_CUTOUTS = {"ion": 3}
SPARE_L = 46.0            # the spare bay: no device chosen yet
INNER_FILLET_R = 6.0      # vertical inside corners of the bays
FLOOR_FILLET_R = 3.0      # where every bay wall meets the floor
# The tray's outer wall runs this far (horizontally) clear of the base's
# inner wall, more than a fit clearance, so the ledge sets the tray's height
# rather than the two tapers wedging together.
TRAY_GAP = P.CLR_FIT + 0.3
TRAY_SINK = 0.3           # tray rim below the base rim: the lid lands on the base
LID_SLOPE_H = 5.0         # the lid's lower band, continuing the base's slope
LIP_H = 3.0               # its flared top band
LID_H = LID_SLOPE_H + LIP_H
LIP_W_MAX = 2.0           # how far the lip stands proud of the slope, bed allowing
BED_MARGIN = 0.25         # the lid is the widest part; keep it this far inside the bed


@dataclass(frozen=True)
class Bay:
    """A bay's floor rectangle, tray coordinates, and which of its sides
    (-X, +X, -Y, +Y) lie on the tray's sloped outer wall."""
    name: str
    x0: float
    x1: float
    y0: float
    y1: float
    sloped: tuple[bool, bool, bool, bool]

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


# Left bay: the ROAM, long axis along Y, its cutout at the -Y end.  Right
# column, stacked -Y to +Y: spare, TRACKR, Ion, long axes along X, lying
# against the partition with their cutouts at the +X end.
_LEFT_W = m.ROAM.width + P.CLR_BAY_OUTER + P.CLR_BAY
_LEFT_L = CUTOUT_INSET + CUTOUT[0] + CUTOUT_GAP + m.ROAM.length + P.CLR_BAY_OUTER
_RIGHT_W = (max(d.length for d in (m.ION, m.TRACKR))
            + P.CLR_BAY + CUTOUT_GAP + CUTOUT[0] + CUTOUT_INSET)
_TRACKR_L = m.TRACKR.width + 2 * P.CLR_BAY
_ION_L = m.ION.width + P.CLR_BAY + P.CLR_BAY_OUTER
_RIGHT_L = SPARE_L + P.WALL + _TRACKR_L + P.WALL + _ION_L
BAY_L = max(_LEFT_L, _RIGHT_L)          # the shorter column is stretched to match
FLOOR_X = _LEFT_W + P.WALL + _RIGHT_W   # the bays and the partition, at the floor
FLOOR_Y = BAY_L

_X0, _Y0 = -FLOOR_X / 2, -FLOOR_Y / 2
_XR = _X0 + _LEFT_W + P.WALL
_Y_TRACKR = _Y0 + SPARE_L + P.WALL
_Y_ION = _Y_TRACKR + _TRACKR_L + P.WALL
BAYS: dict[str, Bay] = {
    "roam": Bay("roam", _X0, _X0 + _LEFT_W, _Y0, -_Y0, (True, False, True, True)),
    "spare": Bay("spare", _XR, -_X0, _Y0, _Y0 + SPARE_L, (False, True, True, False)),
    "trackr": Bay("trackr", _XR, -_X0, _Y_TRACKR, _Y_TRACKR + _TRACKR_L,
                  (False, True, False, False)),
    "ion": Bay("ion", _XR, -_X0, _Y_ION, -_Y0, (False, True, False, True)),
}

# --- heights ------------------------------------------------------------------
TRAY_H = P.TRAY_PLATE + P.BAY_DEPTH
BASE_H = P.FLOOR + m.CHARGER.height + CABLE_ROOM + TRAY_SINK + TRAY_H
TRAY_Z0 = BASE_H - TRAY_SINK - TRAY_H   # the tray's underside, base coordinates

# --- outlines -----------------------------------------------------------------
_TRAY_WALL_H = taper.horiz(P.THIN_WALL)
_BASE_WALL_H = taper.horiz(P.WALL)
_TRAY_GROW = _TRAY_WALL_H + P.BAY_DEPTH * taper.TAN      # floor -> tray rim
_RIM_GROW = TRAY_GAP + _BASE_WALL_H + TRAY_SINK * taper.TAN  # tray rim -> base rim
# The tray's outer face at its rim (tray coordinates), and the base's at its
# rim.  One corner centre serves both, so the gap is uniform through the
# corners; CORNER_R is the base rim's.
TRAY_OUTLINE = taper.Outline(FLOOR_X + 2 * _TRAY_GROW, FLOOR_Y + 2 * _TRAY_GROW,
                             P.CORNER_R - _RIM_GROW, z_ref=TRAY_H)
RIM = taper.Outline(TRAY_OUTLINE.sx + 2 * _RIM_GROW, TRAY_OUTLINE.sy + 2 * _RIM_GROW,
                    P.CORNER_R, z_ref=BASE_H)
# The lid is the widest part: the lip gives way to the bed if it has to.
_SLOPE_TOP = RIM.at(BASE_H + LID_SLOPE_H)
LIP_W = min(LIP_W_MAX,
            (P.BED_X - _SLOPE_TOP[0]) / 2 - BED_MARGIN,
            (P.BED_Y - _SLOPE_TOP[1]) / 2 - BED_MARGIN)

# --- what lies in the bays ------------------------------------------------------
DEVICES = {"roam": m.ROAM, "trackr": m.TRACKR, "ion": m.ION}


def device_footprint(name: str) -> tuple[float, float, float, float]:
    """(x0, x1, y0, y1) of a device lying in its bay, tray coordinates."""
    b = BAYS[name]
    d = DEVICES[name]
    if name == "roam":   # just past its cutout at the -Y end
        x0 = b.x0 + P.CLR_BAY_OUTER
        y0 = b.y0 + CUTOUT_INSET + CUTOUT[0] + CUTOUT_GAP
        return x0, x0 + d.width, y0, y0 + d.length
    x0 = b.x0 + P.CLR_BAY          # against the partition
    y0 = b.y0 + P.CLR_BAY
    return x0, x0 + d.length, y0, y0 + d.width


def cutouts() -> list[tuple[str, float, float, float, float]]:
    """(bay, cx, cy, sx, sy) of every cable cutout, tray coordinates."""
    b = BAYS["roam"]
    out = [("roam", b.cx, b.y0 + CUTOUT_INSET + CUTOUT[0] / 2, CUTOUT[1], CUTOUT[0])]
    for name in ("spare", "trackr", "ion"):
        b = BAYS[name]
        n = UNDERSIDE_PORT_CUTOUTS.get(name, 1)
        if n == 1:
            xs = [b.x1 - CUTOUT_INSET - CUTOUT[0] / 2]
        else:
            step = (b.x1 - b.x0 - 2 * CUTOUT_INSET) / n
            xs = [b.x0 + CUTOUT_INSET + step * (i + 0.5) for i in range(n)]
        out += [(name, x, b.cy, CUTOUT[0], CUTOUT[1]) for x in xs]
    return out
```

- [ ] **Step 8: Run the whole suite**

Run: `uv run pytest -q`
Expected: all pass -- the new tests, and every v1 test through the `V1_*` copies.

- [ ] **Step 9: Commit**

```bash
git add -A src/dock tests docs/measuring.md
git commit -m "Tapered dock: design rules, charger corner radius, taper and layout helpers"
```

---

### Task 3: Hinge and hinge coupon

**Files:**
- Create: `src/dock/hinge.py`, `tests/printability.py`, `tests/test_hinge.py`
- Modify: `src/dock/coupon.py`, `tests/test_coupon.py`, `scripts/export_all.py`

**Interfaces:**
- Consumes: `layout.TRAY_OUTLINE`, `layout.RIM`, `layout.BASE_H`, `layout.LID_H`; `taper.TAN/COS/horiz`; `params.TAPER_DEG`, `WALL`, `LID_PLATE`.
- Produces: `hinge.AXIS_Y`, `AXIS_Z`, `STATIONS`, `PIN_R`, `PIN_FLAT`, `BORE_R`, `SNAP`, `MOUTH_W`, `MOUTH_DEG`, `KNUCKLE_R`, `RELIEF_R`, `HOOK_W`, `CHEEK_W`, `SIDE_CLR`, `OPEN_DEG`, `HEEL_DEG`; `hinge.hull2d(points)`, `hinge.x_cylinder(r, x0, x1) -> Part`, `hinge.opened(deg=0.0) -> Location`, `hinge.wall_gap(y, z)`, `hinge.base_knuckles(stations=STATIONS)`, `hinge.base_relief(stations=STATIONS)`, `hinge.lid_relief(stations=STATIONS)`, `hinge.lid_hooks(stations=STATIONS)`, `hinge.heel_tab()` -- all Parts in base coordinates, lid pieces in the closed position. `printability.steep_faces(part, limit_deg=45.0)`, `printability.span(face)`, `printability.overhang_deg(face)`. `coupon.build_hinge_coupon() -> (base_side, lid_side)`.

- [ ] **Step 1: Write the test helper and the failing tests**

`tests/printability.py`:

```python
"""Shared printability probe: which faces of a part, as it sits on the bed,
point down more steeply than a printer can lay plastic over air."""
import math


def overhang_deg(face) -> float:
    """How far `face` leans past vertical toward facing straight down:
    0 for a wall, 90 for a flat ceiling; negative for a face that looks up."""
    return math.degrees(math.asin(max(-1.0, min(1.0, -face.normal_at().Z))))


def steep_faces(part, limit_deg: float = 45.0) -> list:
    """Every downward face steeper than `limit_deg`, except the bed face."""
    bed = part.bounding_box().min.Z
    return [f for f in part.faces()
            if overhang_deg(f) > limit_deg + 1e-6
            and abs(f.center().Z - bed) > 1e-6]


def span(face) -> float:
    """The longer horizontal side of a face's bounding box: what a bridge
    over it would have to span."""
    s = face.bounding_box().size
    return max(s.X, s.Y)
```

`tests/test_hinge.py`:

```python
"""Hinge pieces measured on their own; the swing is in test_assembly."""
import math

from build123d import Align, Box, Pos, Rot

from dock import hinge as H, layout as L
from printability import span, steep_faces

MAX_BRIDGE = 20.0


def _along_axis(x0, x1, r):
    return H.x_cylinder(r, x0, x1)


def test_hull2d_drops_interior_points():
    pts = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]
    assert sorted(H.hull2d(pts)) == [(0, 0), (0, 2), (2, 0), (2, 2)]


def test_two_stations_each_one_solid():
    assert len(H.base_knuckles().solids()) == 2
    assert len(H.lid_hooks().solids()) == 2


def test_the_pin_sits_in_the_bore_with_clearance():
    assert (H.base_knuckles() & H.lid_hooks()).volume < 1e-6


def test_the_bore_is_clear_to_its_radius():
    for xs in H.STATIONS:
        x0, x1 = xs - H.HOOK_W / 2, xs + H.HOOK_W / 2
        hooks = H.lid_hooks()
        assert (_along_axis(x0, x1, H.BORE_R - 0.02) & hooks).volume < 1e-6
        assert (_along_axis(x0, x1, H.BORE_R + 0.1) & hooks).volume > 1e-3


def _mouth_probe(xs, width):
    """A bar from the axis out along the mouth, `width` across."""
    a = H.MOUTH_DEG
    bar = Box(H.HOOK_W, H.KNUCKLE_R + 2.0, width, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return Pos(xs, H.AXIS_Y, H.AXIS_Z) * Rot(a, 0, 0) * bar


def test_the_mouth_neck_is_narrower_than_the_pin_by_the_snap():
    hooks = H.lid_hooks()
    for xs in H.STATIONS:
        assert (_mouth_probe(xs, H.MOUTH_W - 0.02) & hooks).volume < 1e-6
        assert (_mouth_probe(xs, H.MOUTH_W + 0.1) & hooks).volume > 1e-4
    assert H.MOUTH_W < 2 * H.PIN_R


def test_the_pin_underside_is_a_short_bridge_and_the_cheeks_print_unsupported():
    steep = steep_faces(H.base_knuckles())
    assert steep, "expected the pins' flat undersides"
    for f in steep:
        assert span(f) <= MAX_BRIDGE
        assert math.isclose(f.center().Z, H.AXIS_Z - H.PIN_FLAT * H.PIN_R, abs_tol=1e-6)


def test_the_axis_is_behind_the_rim_and_the_knuckle_sweep_clears_the_tray():
    assert H.AXIS_Y > L.RIM.sy / 2
    assert H.AXIS_Y - H.RELIEF_R > L.TRAY_OUTLINE.sy / 2


def test_opened_turns_the_lid_up_and_back():
    y, z = H.AXIS_Y - 10.0, H.AXIS_Z          # a point on the lid, 10 mm in front of the axis
    p = H.opened(90.0) * Pos(0, y, z)
    assert math.isclose(p.position.Y, H.AXIS_Y, abs_tol=1e-6)
    assert math.isclose(p.position.Z, H.AXIS_Z + 10.0, abs_tol=1e-6)
```

Append to `tests/test_coupon.py`:

```python
def test_hinge_coupon_halves_are_single_solids_on_the_bed():
    for p in coupon.build_hinge_coupon():
        assert p.is_valid and len(p.solids()) == 1
        assert abs(p.bounding_box().min.Z) < 1e-6


def test_the_hinge_coupon_prints_like_the_dock_hinge():
    from dock import hinge
    from printability import span, steep_faces
    base_side, lid_side = coupon.build_hinge_coupon()
    flats = steep_faces(base_side)
    assert len(flats) == 1          # the pin's flat underside, and nothing else
    assert span(flats[0]) <= hinge.HOOK_W + 2 * hinge.SIDE_CLR + 1.0
    for f in steep_faces(lid_side):  # only the mouth's short roof
        assert span(f) <= hinge.HOOK_W + 1e-6
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_hinge.py tests/test_coupon.py -q`
Expected: `No module named 'dock.hinge'`; `build_hinge_coupon` missing.

- [ ] **Step 3: Write `src/dock/hinge.py`**

```python
"""Snap-on, lift-off lid hinge: the base carries the pins, the lid the hooks.

Everything here is in base coordinates, with the lid modelled closed on the
rim; lid.py turns the lid over for printing.  The axis runs along X at rim
height, AXIS_Y behind the +Y rim -- far enough that nothing near it sweeps
into the tray.  Two stations stand HINGE_INSET in from each end.

At each station the base carries two cheeks with a pin between them.  A
cheek is a disc round the axis hulled with a 45 degree chin that runs down
into the wall, so it prints open-top-up without supports; the pin's
underside is cut flat at PIN_FLAT*PIN_R, a 3 mm bridge, which keeps it
inside the bore circle.

The lid carries a hook between the cheeks: a ring round the pin (a teardrop
bore, point up as printed) hulled into the lid's back wall and top, so it
prints top-down.  Its mouth has a neck SNAP narrower than the pin and then
flares.  The mouth points MOUTH_DEG above +Y with the lid closed, which at
OPEN_DEG is straight down the base's outer wall: at full open the lid lifts
off along the wall, snapping the neck over the pin.  Lift a closed lid and
the pin goes to the bottom of the bore instead, so it stays on.

A heel tab at X = 0 stops the lid at OPEN_DEG: its tip lands on the base's
outer wall there.  It is its own piece rather than part of a hook, so the
mouths can face where they must.

Each part's knuckles turn inside relief discs (RELIEF_R round the axis) cut
out of the other part.  A disc round the axis is the same at every angle, so
the swing clears however far the lid turns.
"""
import math

from build123d import Align, Box, Cylinder, Location, Part, Plane, Polygon, Pos, Rot, extrude

from dock import layout as L
from dock import params as P
from dock import taper

PIN_R = 2.5
PIN_FLAT = 0.8            # pin underside cut flat this far (x PIN_R) below the axis
BORE_CLR = 0.3            # tune on the hinge coupon
BORE_R = PIN_R + BORE_CLR
SNAP = 0.4                # neck narrower than the pin by this; tune on the coupon
MOUTH_W = 2 * PIN_R - SNAP
THROAT = 1.0              # neck length past the bore before the mouth flares
KNUCKLE_R = 5.5
RELIEF_R = KNUCKLE_R + 0.5
HOOK_W = 8.0
CHEEK_W = 4.0
SIDE_CLR = 0.3            # hook to cheek, along X
HINGE_INSET = 60.0        # station centre in from each end of the rim
OPEN_DEG = 110.0
MOUTH_DEG = OPEN_DEG - 90.0 - P.TAPER_DEG   # closed-lid mouth angle, from +Y toward +Z
HEEL_R = 7.0              # heel tip centre, from the axis
HEEL_TIP_R = 1.0
HEEL_W = 8.0
AXIS_GAP = 0.2            # knuckle sweep to tray, at the rim

AXIS_Y = L.TRAY_OUTLINE.sy / 2 + RELIEF_R + AXIS_GAP
AXIS_Z = L.BASE_H
STATIONS = (-(L.RIM.sx / 2 - HINGE_INSET), L.RIM.sx / 2 - HINGE_INSET)

_RIM_Y = L.RIM.sy / 2
_BASE_WALL_H = taper.horiz(P.WALL)
_LID_WALL_Y = _RIM_Y - 0.3          # inside the lid's back wall at every height of it
_LID_TOP = L.BASE_H + L.LID_H
_ALONG = (Align.CENTER, Align.CENTER, Align.MIN)


def hull2d(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Convex hull, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted(set((round(a, 9), round(b, 9)) for a, b in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    upper: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _circle(cy: float, cz: float, r: float, n: int = 48) -> list[tuple[float, float]]:
    return [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def _polar(r: float, deg: float) -> tuple[float, float]:
    """(Y, Z) of the point `r` from the axis at `deg` above +Y."""
    a = math.radians(deg)
    return AXIS_Y + r * math.cos(a), AXIS_Z + r * math.sin(a)


def _prism(points_yz, x0: float, x1: float) -> Part:
    """A YZ polygon extruded along X from x0 to x1."""
    return extrude(Plane.YZ.offset(x0) * Polygon(*points_yz, align=None), amount=x1 - x0)


def x_cylinder(r: float, x0: float, x1: float) -> Part:
    """A cylinder of radius r round the hinge axis, from x0 to x1."""
    return Pos(x0, AXIS_Y, AXIS_Z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=_ALONG)


def opened(deg: float = 0.0) -> Location:
    """Turns a closed lid, in base coordinates, `deg` open about the axis."""
    return Pos(0, AXIS_Y, AXIS_Z) * Rot(-deg, 0, 0) * Pos(0, -AXIS_Y, -AXIS_Z)


def wall_gap(y: float, z: float) -> float:
    """Signed distance from (y, z) to the base's +Y outer face, outside > 0."""
    return ((y - _RIM_Y) + (L.BASE_H - z) * taper.TAN) * taper.COS


def _heel_closed_deg() -> float:
    """Where the heel tip points with the lid closed: the angle that puts it
    HEEL_TIP_R off the outer wall when the lid is at OPEN_DEG."""
    lo, hi = -175.0, -95.0      # wall_gap at hi is > HEEL_TIP_R, at lo < it
    for _ in range(60):
        mid = (lo + hi) / 2
        if wall_gap(*_polar(HEEL_R, mid)) > HEEL_TIP_R:
            hi = mid
        else:
            lo = mid
    return hi + OPEN_DEG


HEEL_DEG = _heel_closed_deg()


def _gap_ends(xs: float) -> tuple[float, float]:
    """X of the two cheek faces either side of the hook at station xs."""
    return xs - HOOK_W / 2 - SIDE_CLR, xs + HOOK_W / 2 + SIDE_CLR


def _cheek_profile() -> list[tuple[float, float]]:
    ty, tz = _polar(KNUCKLE_R, -45.0)        # where the 45-degree chin leaves the disc
    mid = _RIM_Y - _BASE_WALL_H / 2          # the wall's mid-surface at the rim
    # run the chin down-and-in at 45 degrees until it meets that mid-surface
    zw = (mid - L.BASE_H * taper.TAN - ty + tz) / (1 - taper.TAN)
    yw = ty - (tz - zw)
    return hull2d(_circle(AXIS_Y, AXIS_Z, KNUCKLE_R) + [(yw, zw), (mid, AXIS_Z)])


def base_knuckles(stations=STATIONS) -> Part:
    """The cheeks and pins, to be added to the base."""
    prof = _cheek_profile()
    part = None
    for xs in stations:
        a, b = _gap_ends(xs)
        flat = Pos(xs, AXIS_Y, AXIS_Z - PIN_FLAT * PIN_R) * Box(
            b - a + 2, 2 * PIN_R + 1, PIN_R, align=(Align.CENTER, Align.CENTER, Align.MAX))
        pin = x_cylinder(PIN_R, a - 0.5, b + 0.5) - flat
        station = _prism(prof, a - CHEEK_W, a) + _prism(prof, b, b + CHEEK_W) + pin
        part = station if part is None else part + station
    return part


def base_relief(stations=STATIONS) -> Part:
    """What the base gives up so the hooks can turn."""
    part = None
    for xs in stations:
        c = x_cylinder(RELIEF_R, *_gap_ends(xs))
        part = c if part is None else part + c
    return part


def lid_relief(stations=STATIONS) -> Part:
    """What the lid gives up so it can turn round the cheeks."""
    part = None
    for xs in stations:
        a, b = _gap_ends(xs)
        for c in (x_cylinder(RELIEF_R, a - CHEEK_W - SIDE_CLR, a + SIDE_CLR),
                  x_cylinder(RELIEF_R, b - SIDE_CLR, b + CHEEK_W + SIDE_CLR)):
            part = c if part is None else part + c
    return part


def _mouth_profile() -> list[tuple[float, float]]:
    a = math.radians(MOUTH_DEG)
    u = (math.cos(a), math.sin(a))
    n = (-math.sin(a), math.cos(a))
    r1, r2 = BORE_R + THROAT, KNUCKLE_R + 3.0
    w1, w2 = MOUTH_W / 2, BORE_R + 0.5
    local = [(0, -w1), (r1, -w1), (r2, -w2), (r2, w2), (r1, w1), (0, w1)]
    return [(AXIS_Y + s * u[0] + t * n[0], AXIS_Z + s * u[1] + t * n[1]) for s, t in local]


def lid_hooks(stations=STATIONS) -> Part:
    """The hooks, closed-lid position, to be added to the lid."""
    k = KNUCKLE_R
    prof = hull2d(_circle(AXIS_Y, AXIS_Z, k) + [
        (_LID_WALL_Y, AXIS_Z), (_LID_WALL_Y, _LID_TOP), (AXIS_Y + k, _LID_TOP)])
    # teardrop: the point is down here, which is up as the lid prints
    bore = hull2d(_circle(AXIS_Y, AXIS_Z, BORE_R) + [(AXIS_Y, AXIS_Z - BORE_R * math.sqrt(2))])
    mouth = _mouth_profile()
    part = None
    for xs in stations:
        x0, x1 = xs - HOOK_W / 2, xs + HOOK_W / 2
        hook = _prism(prof, x0, x1) - _prism(bore, x0 - 1, x1 + 1) - _prism(mouth, x0 - 1, x1 + 1)
        part = hook if part is None else part + hook
    return part


def heel_tab() -> Part:
    """The stop, closed-lid position, to be added to the lid at X = 0."""
    ty, tz = _polar(HEEL_R, HEEL_DEG)
    prof = hull2d(_circle(ty, tz, HEEL_TIP_R, 16) + [
        (ty + HEEL_TIP_R, _LID_TOP), (_LID_WALL_Y, _LID_TOP),
        (_LID_WALL_Y, _LID_TOP - P.LID_PLATE)])
    return _prism(prof, -HEEL_W / 2, HEEL_W / 2)
```

- [ ] **Step 4: Add the hinge coupon**

Replace `src/dock/coupon.py` with:

```python
"""Calibration coupons.

`build_coupon`: one plate with six graded holes and one peg, for the fit
clearances in params.py.

`build_hinge_coupon`: one hinge station on a short stretch of wall and of
lid, for BORE_CLR and SNAP in hinge.py.  Print both halves, snap the hook
onto the pin by pulling it along the mouth, and swing it: tune the numbers
there before the base and lid, which are the two longest prints.
"""
from build123d import Align, Box, Part, Pos, Rot

from dock import hinge as H
from dock import layout as L

CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)
PEG = 10.0
PITCH = 16.0
THICK = 4.0

HINGE_SPAN = H.HOOK_W + 2 * (H.SIDE_CLR + H.CHEEK_W) + 6.0
_WALL_BLOCK = (8.0, 22.0)     # depth into the dock, height: holds the cheeks' chins
_LID_BLOCK = 12.0             # depth of lid behind the hook


def build_coupon() -> tuple[Part, Part]:
    n = len(CLEARANCES)
    plate = Box(PITCH * n + 6, PITCH + 6, THICK, align=(Align.MIN, Align.MIN, Align.MIN))
    for i, c in enumerate(CLEARANCES):
        hole = Box(PEG + 2 * c, PEG + 2 * c, THICK, align=(Align.CENTER, Align.CENTER, Align.MIN))
        plate -= Pos(3 + PITCH * i + PITCH / 2, 3 + PITCH / 2, 0) * hole
    # orientation notch beside the tightest hole
    plate -= Pos(0, 0, 0) * Box(3, 3, THICK, align=(Align.MIN, Align.MIN, Align.MIN))
    peg = Box(PEG, PEG, THICK * 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return plate, peg


def build_hinge_coupon() -> tuple[Part, Part]:
    """(base side, lid side), each on the bed as it prints."""
    st = (0.0,)
    y_rim = L.RIM.sy / 2
    depth, height = _WALL_BLOCK
    wall = Pos(0, y_rim - depth, H.AXIS_Z - height) * Box(
        HINGE_SPAN, depth, height, align=(Align.CENTER, Align.MIN, Align.MIN))
    base_side = wall - H.base_relief(st) + H.base_knuckles(st)
    base_side = Pos(0, -y_rim, -(H.AXIS_Z - height)) * base_side
    top = H.AXIS_Z + L.LID_H
    plate = Pos(0, y_rim - _LID_BLOCK, H.AXIS_Z) * Box(
        HINGE_SPAN, _LID_BLOCK, L.LID_H, align=(Align.CENTER, Align.MIN, Align.MIN))
    lid_side = plate - H.lid_relief(st) + H.lid_hooks(st)
    lid_side = Pos(0, y_rim, top) * Rot(180, 0, 0) * lid_side      # hook side up, like the lid
    return base_side, lid_side
```

In `scripts/export_all.py`, add after `_coupon_peg`:

```python
def _hinge_coupon_base() -> Part:
    return coupon.build_hinge_coupon()[0]


def _hinge_coupon_lid() -> Part:
    return coupon.build_hinge_coupon()[1]
```

and add to the first `PARTS` dict:

```python
    "hinge_coupon_base": _hinge_coupon_base,
    "hinge_coupon_lid": _hinge_coupon_lid,
```

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -q`
Expected: all pass (test_parts now also checks both hinge coupon halves).

- [ ] **Step 6: Commit**

```bash
git add -A src/dock tests scripts/export_all.py
git commit -m "Hinge: snap-on lift-off pins and hooks, heel stop, and a hinge coupon"
```

---

### Task 4: Lid

**Files:**
- Rewrite: `src/dock/lid.py`, `tests/test_lid.py`
- Delete: `tests/test_assembly.py` (v1; its v2 replacement is Task 7)
- Modify: `scripts/export_all.py` (`build_report`)

**Interfaces:**
- Consumes: `hinge.lid_relief()`, `hinge.lid_hooks()`, `hinge.heel_tab()`, `hinge.opened()`; `layout.RIM`, `BASE_H`, `LID_SLOPE_H`, `LIP_H`, `LID_H`, `LIP_W`.
- Produces: `lid.build_lid() -> Part` (print orientation, top face on the bed), `lid.lid_seat(deg=0.0) -> Location` (printed lid → on the base, `deg` open), `lid.PRINT`, `lid.WALL_H`, `lid.Z_RIM`, `lid.Z_SLOPE`, `lid.Z_TOP`, `lid.LIP`.

- [ ] **Step 1: Retire the v1 lid tests and write the new ones**

```bash
git rm tests/test_lid.py tests/test_assembly.py
```

`tests/test_lid.py`:

```python
"""Lid tests: measured on the built solid, in print orientation and seated."""
import math
from functools import lru_cache

from build123d import Align, Box, Pos

from dock import hinge as H, layout as L, lid, params, taper
from printability import span, steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)


@lru_cache(maxsize=None)
def _printed():
    return lid.build_lid()


@lru_cache(maxsize=None)
def _seated():
    return lid.lid_seat() * _printed()


def _slab(p, z, thick=2e-3):
    return p & (Pos(0, 0, z) * Box(400, 400, thick, align=_CTR))


def _front_y(p, z):
    """Y of the lid's front (-Y) face at height z: clear of the hinge side."""
    return _slab(p, z).bounding_box().min.Y


def test_lid_is_one_valid_solid_on_the_bed():
    p = _printed()
    assert p.is_valid and len(p.solids()) == 1
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_lid_fits_the_bed():
    s = _printed().bounding_box().size
    assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_the_lid_meets_the_rim_flush():
    z = L.BASE_H + 0.01
    sx, sy, _ = L.RIM.at(z)
    bb = _slab(_seated(), z).bounding_box()
    assert math.isclose(bb.size.X, sx, abs_tol=0.02)
    assert math.isclose(bb.min.Y, -sy / 2, abs_tol=0.02)


def test_the_slope_continues_the_base_taper():
    z0, z1 = L.BASE_H + 0.5, L.BASE_H + L.LID_SLOPE_H - 0.5
    lean = (_front_y(_seated(), z0) - _front_y(_seated(), z1)) / (z1 - z0)
    assert math.isclose(lean, taper.TAN, abs_tol=1e-3)


def test_the_lip_stands_proud_of_the_slope():
    z_slope = L.BASE_H + L.LID_SLOPE_H
    below = _front_y(_seated(), z_slope - 0.01)
    above = _front_y(_seated(), z_slope + 0.5)
    assert math.isclose(below - above, L.LIP_W, abs_tol=0.02)


def test_the_walls_are_a_thin_wall_thick_square_to_the_slope():
    z = L.BASE_H + 2.0
    y_out = -L.RIM.at(z)[1] / 2
    w = lid.WALL_H
    probe = lambda y, t: Pos(0, y, z) * Box(4, t, 0.02, align=_CTR)
    assert (probe(y_out + w / 2, w - 0.1) & _seated()).volume >= probe(0, w - 0.1).volume * (1 - 1e-4)
    assert (probe(y_out + w + 0.1, 0.1) & _seated()).volume < 1e-9


def test_the_plate_is_lid_plate_thick():
    top = L.BASE_H + L.LID_H
    col = lambda z0, z1: Pos(0, 0, z0) * Box(2, 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    solid = col(top - params.LID_PLATE + 0.02, top - 0.02)
    air = col(L.BASE_H + 0.5, top - params.LID_PLATE - 0.02)
    assert (solid & _seated()).volume >= solid.volume * (1 - 1e-4)
    assert (air & _seated()).volume < 1e-6


def test_the_lid_prints_with_only_the_hook_mouth_roofs_overhanging():
    for f in steep_faces(_printed()):
        c = f.center()
        near = min(abs(c.X - xs) for xs in H.STATIONS)
        assert near <= H.HOOK_W / 2 + 1e-6, f"overhang away from a hook at {c}"
        assert span(f) <= H.HOOK_W + 1e-6


def test_the_lid_is_relieved_round_the_base_cheeks():
    for xs in H.STATIONS:
        a = xs - H.HOOK_W / 2 - H.SIDE_CLR
        probe = H.x_cylinder(H.RELIEF_R - 0.05, a - H.CHEEK_W, a)
        assert (probe & _seated()).volume < 1e-6
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_lid.py -q`
Expected: failures -- the v1 lid has no `lid_seat` taking an angle, no hinge, no lip.

- [ ] **Step 3: Write `src/dock/lid.py`**

```python
"""Lid: a shallow hinged cap that carries the base's taper up past the rim.

Its lower LID_SLOPE_H continues the base's 15 degree slope from the rim; its
top LIP_H is a lip standing LIP_W proud of that slope -- the finger grip for
opening it, and the reference's flared lid edge.  It sits flush on the rim
with no skirt: the hinge locates it.  Walls THIN_WALL, top LID_PLATE.

It is modelled closed on the base, in base coordinates, which is where the
hinge pieces are built, then turned over about X (PRINT) to print top face
down: its walls lean inward as they rise from the bed, so nothing
overhangs but the hook mouths' short roofs.  `lid_seat(deg)` puts the
printed part back on the base, `deg` open.
"""
from build123d import Location, Part, Plane, Pos, RectangleRounded, Rot, Sketch, extrude, loft

from dock import hinge as H
from dock import layout as L
from dock import params as P
from dock import taper

WALL_H = taper.horiz(P.THIN_WALL)
Z_RIM = L.BASE_H
Z_SLOPE = Z_RIM + L.LID_SLOPE_H
Z_TOP = Z_RIM + L.LID_H
LIP = L.RIM.at(Z_SLOPE, -L.LIP_W)              # (sx, sy, r) of the lip
PRINT = Pos(0, 0, Z_TOP) * Rot(180, 0, 0)      # closed on the base -> top face on the bed


def _rr(sx: float, sy: float, r: float, z: float) -> Sketch:
    return Plane.XY.offset(z) * RectangleRounded(sx, sy, r)


def _closed() -> Part:
    sx, sy, r = LIP
    c = P.CHAMFER
    body = L.RIM.solid(Z_RIM, Z_SLOPE)
    body += extrude(_rr(sx, sy, r, Z_SLOPE), amount=L.LIP_H - c)
    # the top edge is the bed edge as printed: chamfered, not filleted
    body += loft([_rr(sx, sy, r, Z_TOP - c), _rr(sx - 2 * c, sy - 2 * c, r - c, Z_TOP)])
    body -= L.RIM.solid(Z_RIM - 1.0, Z_TOP - P.LID_PLATE, inset=WALL_H)
    body -= H.lid_relief()
    return body + H.lid_hooks() + H.heel_tab()


def build_lid() -> Part:
    return PRINT * _closed()


def lid_seat(deg: float = 0.0) -> Location:
    """Moves the printed lid onto the base, `deg` open."""
    return H.opened(deg) * PRINT.inverse()
```

- [ ] **Step 4: Report sizes off the built parts**

The v1 `build_report` reads `lid.LID_X`, which is gone. In `scripts/export_all.py`, add `from dock import hinge` and `from dock import layout` to the imports, and replace `build_report` with:

```python
def build_report() -> str:
    """The derived sizes and clearances, in mm, read off the built parts.
    Every one of them moves on its own when a measurement or a design rule
    changes, so print them where they can be read before a long print."""
    lines = ["build report (mm, as printed)"]
    for name in ("base", "tray", "lid"):
        s = PARTS[name]().bounding_box().size
        lines.append(f"  {name:<5}{s.X:8.2f} x {s.Y:7.2f} x {s.Z:6.2f}")
    lines += [
        f"  charger fence: {base.FENCE_MARGIN_Y:.2f} free each side; port room "
        f"{base.PORT_PLUG_ROOM:.2f} (need {base.PORT_PLUG_ROOM_MIN:.2f})",
        f"  lid lip {layout.LIP_W:.2f} proud; hinge opens to {hinge.OPEN_DEG:.0f} deg",
    ]
    return "\n".join(lines)
```

- [ ] **Step 5: Run the whole suite and the export**

Run: `uv run pytest -q && uv run python scripts/export_all.py`
Expected: all pass; the report lists the lid at about 249.5 × 192.3 × 13.5 (base and tray are still v1).

- [ ] **Step 6: Commit**

```bash
git add -A src/dock/lid.py tests scripts/export_all.py
git commit -m "Lid: tapered hinged cap with a flared lip, printed top-down"
```

---

### Task 5: Base

**Files:**
- Rewrite: `src/dock/base.py`, `tests/test_base.py`

**Interfaces:**
- Consumes: `hinge.base_relief()`, `hinge.base_knuckles()`, `hinge.STATIONS`, `hinge.x_cylinder()`; `layout.RIM`, `BASE_H`, `TRAY_Z0`; `taper.*`; `measurements.CHARGER` (incl. `corner_r`), `CORD_END`.
- Produces: `base.build_base() -> Part`, `base.tray_seat() -> Location`; constants read by tests and the report: `WALL_H`, `LEDGE_W`, `LEDGE_Z`, `GROOVE_D`, `GROOVE_UP`, `FENCE_H`, `FENCE_Y`, `POCKET_*`, `CAVITY_MIN_X/MAX_X`, `FENCE_MIN_X/MAX_X`, `PORT_PLUG_ROOM(_MIN)`, `FENCE_MARGIN_Y`, `CORD_W/H/Z0`, `SUPPORTED_CEILINGS`, `ESCAPE_L/H/Y/ZC/FLAT_Y`, `TIE_*`, `TIE_HOLES`, `FOOT_*`, `FOOT_CENTRES`.

- [ ] **Step 1: Write the new tests**

Replace `tests/test_base.py` with:

```python
"""Base tests: everything read off the built solid."""
import math
from functools import lru_cache

from build123d import Align, Axis, Box, Cylinder, Pos, fillet

from dock import measurements as m
from dock import base, hinge as H, layout as L, params, taper
from printability import span, steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX_BRIDGE = 20.0


@lru_cache(maxsize=None)
def _base():
    return base.build_base()


def _slab(p, z, thick=2e-3):
    return p & (Pos(0, 0, z) * Box(400, 400, thick, align=_CTR))


def _section_face(p, z):
    """The part's cross-section at height z, as one face: the biggest
    upward face of a hair-thin slab there."""
    faces = [f for f in _slab(p, z).faces() if f.normal_at().Z > 0.99]
    return max(faces, key=lambda f: f.area)


def _solid(probe):
    return (probe & _base()).volume >= probe.volume * (1 - 1e-4)


def _clear(probe):
    return (probe & _base()).volume < probe.volume * 1e-6


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=_CTR)


def _charger(dx=0.0, dy=0.0):
    c = m.CHARGER
    body = Box(c.port_to_inlet, c.port_face_width, c.height, align=(Align.MIN, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Z), c.corner_r)
    return Pos(base.POCKET_MIN_X + params.CLR_FIT + dx, dy, params.FLOOR) * body


# --- shell --------------------------------------------------------------------

def test_base_is_one_valid_solid_on_the_bed_and_fits_it():
    p = _base()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert bb.size.X <= params.BED_X and bb.size.Y <= params.BED_Y


def test_the_rim_is_the_layout_rim():
    z = L.BASE_H - 0.01
    sx, sy, _ = L.RIM.at(z)
    bb = _slab(_base(), z).bounding_box()
    assert math.isclose(bb.size.X, sx, abs_tol=0.02)
    assert math.isclose(bb.min.Y, -sy / 2, abs_tol=0.02)
    assert _clear(_box(0, -sy / 2 + 1.0, L.BASE_H + 0.5, 10, 1, 0.5))


def test_every_side_leans_at_the_draft():
    for axis, z0, z1 in (("-Y", 20, 70), ("+X", 20, 70), ("-X", 30, 70)):
        def edge(z):
            bb = _slab(_base(), z).bounding_box()
            return {"-Y": -bb.min.Y, "+X": bb.max.X, "-X": -bb.min.X}[axis]
        lean = (edge(z1) - edge(z0)) / (z1 - z0)
        assert math.isclose(lean, taper.TAN, abs_tol=1e-3), axis


def test_corners_run_from_r30_at_the_rim_toward_r8_at_the_foot():
    from build123d import GeomType
    for z in (L.BASE_H - 1.0, params.CHAMFER + 1.0):
        top = _section_face(_base(), z)
        radii = [e.radius for e in top.outer_wire().edges() if e.geom_type == GeomType.CIRCLE]
        assert math.isclose(max(radii), L.RIM.at(z)[2], abs_tol=0.02), z
    assert L.RIM.at(0.0)[2] > 7.5


def test_the_wall_is_one_wall_thick_square_to_the_slope():
    z = 60.0
    top = _section_face(_base(), z)
    outer = top.outer_wire().bounding_box().min.Y
    inner = min(w.bounding_box().min.Y for w in top.inner_wires())
    assert math.isclose((inner - outer) * taper.COS, params.WALL, abs_tol=0.02)


def test_the_floor_is_floor_thick():
    x = base.FENCE_MAX_X + 20.0 + base.TIE_PITCH / 2   # between tie holes
    assert _solid(_box(x, 0, params.FLOOR / 2, 1, 1, params.FLOOR - 0.04))
    assert _clear(_box(x, 0, params.FLOOR + 1.0, 1, 1, 1.0))


# --- tray ledge ---------------------------------------------------------------

def test_the_ledge_is_a_ledge_wide_shelf_at_the_tray_underside():
    z = base.LEDGE_Z
    below = _slab(_base(), z - 0.01)
    top = _section_face(_base(), z - 0.01)
    shelf = min(w.bounding_box().min.Y for w in top.inner_wires())
    wall = L.RIM.at(z, taper.horiz(params.WALL))[1] / 2
    assert math.isclose(shelf + wall, base.LEDGE_W, abs_tol=0.03)
    assert _clear(_box(0, -wall + 1.0, z + 0.5, 20, 1.0, 0.5))


# --- colour groove ------------------------------------------------------------

def test_the_colour_groove_is_cut_at_the_band_height():
    def front(z):
        return -_slab(_base(), z).bounding_box().min.Y
    sy = lambda z: L.RIM.at(z)[1] / 2
    assert math.isclose(sy(params.BAND_H) - front(params.BAND_H), base.GROOVE_D, abs_tol=0.02)
    for z in (params.BAND_H - 1.0, params.BAND_H + 1.5):
        assert math.isclose(front(z), sy(z), abs_tol=0.02)


# --- charger fence --------------------------------------------------------------

def test_the_charger_fits_the_pocket_with_fit_clearance():
    assert (_charger() & _base()).volume < 1e-6
    assert (_charger(dx=params.CLR_FIT + 0.1) & _base()).volume > 1e-3
    assert (_charger(dy=params.CLR_FIT + 0.1) & _base()).volume > 1e-3
    assert (_charger(dx=-(base.POCKET_BACK_SLACK + params.CLR_FIT + 0.1)) & _base()).volume > 1e-3


def test_the_pocket_corners_follow_the_charger_corners():
    c = m.CHARGER
    x = base.POCKET_MAX_X
    y = base.POCKET_Y / 2
    d = 0.2 * base.POCKET_R           # inside the fillet: solid; a square corner would be air
    assert _solid(_box(x - d, y - d, params.FLOOR + 1.0, 0.1, 0.1, 0.5))


def test_the_fence_has_no_fingernail_notch():
    y = base.POCKET_Y / 2 + params.WALL / 2
    x0, x1 = base.FENCE_MIN_X + 2.0, base.POCKET_MAX_X - base.POCKET_R
    assert _solid(_box((x0 + x1) / 2, y, params.FLOOR + base.FENCE_H / 2, x1 - x0, 0.5, base.FENCE_H - 0.2))


def test_room_in_front_of_the_ports_for_the_plugs():
    x = base.POCKET_MAX_X + params.WALL + 0.5
    room = base.CAVITY_MAX_X - base.POCKET_MAX_X
    assert room >= base.PORT_PLUG_ROOM_MIN
    probe = _box(x + (room - params.WALL - 1.0) / 2, 0, params.FLOOR + 5.0,
                 room - params.WALL - 1.0, 20.0, 8.0)
    assert _clear(probe)


# --- wall openings ----------------------------------------------------------------

def _through_minus_x(y, z, sy, sz):
    x0 = -L.RIM.sx / 2 - 1.0
    return Pos(x0, y, z) * Box(base.CAVITY_MIN_X - x0 + 0.5, sy, sz, align=(Align.MIN, Align.CENTER, Align.CENTER))


def test_the_cord_port_goes_through_the_minus_x_wall_on_the_inlet():
    z = params.FLOOR + m.CHARGER.inlet_center_z
    assert _clear(_through_minus_x(0, z, base.CORD_W - 0.1, base.CORD_H - 0.1))
    assert not _clear(_through_minus_x(0, z, base.CORD_W + 0.5, base.CORD_H + 0.5))


def test_two_oval_escape_ports_flank_the_charger():
    for s in (-1, 1):
        y, z = s * base.ESCAPE_Y, base.ESCAPE_ZC
        core = _through_minus_x(y, z, base.ESCAPE_L - base.ESCAPE_H, base.ESCAPE_H - 0.1)
        assert _clear(core)
        # a rounded end: the rectangle's corner is still wall
        cx, cz = y + s * (base.ESCAPE_L / 2 - 0.3), z + base.ESCAPE_H / 2 - 0.3
        assert not _clear(_through_minus_x(cx, cz, 0.2, 0.2))
        # clear of the fence, and all on the -X wall's flat
        assert abs(y) - base.ESCAPE_L / 2 > base.FENCE_Y / 2
        assert abs(y) + base.ESCAPE_L / 2 < base.ESCAPE_FLAT_Y
        assert base.ESCAPE_ZC - base.ESCAPE_H / 2 > params.BAND_H + base.GROOVE_UP


# --- floor features -------------------------------------------------------------

def test_tie_holes_go_through_the_floor_and_feet_are_shallow_recesses():
    assert len(base.TIE_HOLES) >= 12
    for x, y in base.TIE_HOLES:
        assert _clear(Pos(x, y, -0.5) * Cylinder(base.TIE_D / 2 - 0.05, params.FLOOR + 1.0, align=_MIN))
    for x, y in base.FOOT_CENTRES:
        assert _clear(Pos(x, y, 0.01) * Cylinder(base.FOOT_R - 0.05, base.FOOT_RECESS_D - 0.02, align=_MIN))
        assert _solid(Pos(x, y, base.FOOT_RECESS_D + 0.02) * Cylinder(base.FOOT_R - 0.05, params.FLOOR - base.FOOT_RECESS_D - 0.04, align=_MIN))


# --- hinge ------------------------------------------------------------------------

def test_the_hinge_pins_and_relief_are_in_the_base():
    for xs in H.STATIONS:
        a, b = xs - H.HOOK_W / 2, xs + H.HOOK_W / 2
        assert _solid(H.x_cylinder(H.PIN_R * 0.5, a, b))
        ring = H.x_cylinder(H.RELIEF_R - 0.05, a, b) - H.x_cylinder(H.PIN_R + 0.05, a - 1, b + 1)
        assert _clear(ring)


# --- printability -----------------------------------------------------------------

def test_no_unsupported_ceilings_but_the_cord_port():
    cord_top = base.CORD_Z0 + base.CORD_H
    for f in steep_faces(_base()):
        c = f.center()
        if abs(c.Z - cord_top) < 1e-6 and c.X < base.CAVITY_MIN_X and math.isclose(f.bounding_box().size.Y, base.CORD_W, abs_tol=1e-6):
            continue
        assert span(f) <= MAX_BRIDGE, f"{span(f):.1f} mm ceiling at {c}"
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_base.py -q`
Expected: failures (no `tray_seat` at a layout height, no escape ports at `ESCAPE_Y`, `layout` rim mismatch, and so on).

- [ ] **Step 3: Write `src/dock/base.py`**

```python
"""Base: the tapered lower shell.  It hides the charger and the cable slack,
carries the tray on a ledge, and the lid on its rim and hinge pins.

The outer faces lean at the draft from the rim (layout.RIM, CORNER_R) down
to the foot, one WALL thick square to the slope, so the corners run from
R30 at the rim to about R8 at the bed.  A V groove at BAND_H is where the
colour changes: dark foot band below, light body above, one tool change
anywhere inside the groove.  Its upper flank is the steeper one, so it
prints.

The tray rests on a ledge ring LEDGE_W proud of the inner wall at the
tray's underside; the ledge's underside leans in, so it prints unsupported.
The tray sits TRAY_SINK below the rim, so the lid lands on the base.

The charger is the v1 arrangement: backed onto the -X end wall in a U
fence, its AC inlet reached from outside through the cord port.  The fence
corners follow the charger's own rounded corners.  Two stadium-shaped
escape ports flank the charger in the same wall, on its flat between the
fence and the corner arcs, above the colour groove.

It prints open-top-up.  The cord port's flat top is too wide to bridge, so
it is the one ceiling printed on supports (SUPPORTED_CEILINGS); everything
else that faces down is a bridge of 20 mm or less: the escape ports' heads,
the foot recesses and the hinge pins' flats.

Base coordinates: XY centred, bed at Z = 0.
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Location, Part, Plane, Pos,
                       SlotCenterToCenter, extrude, fillet, loft)

from dock import hinge as H
from dock import layout as L
from dock import measurements as M
from dock import params as P
from dock import taper

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)

WALL_H = taper.horiz(P.WALL)          # the sloped wall, measured horizontally
BASE_H = L.BASE_H
RIM = L.RIM

# --- tray ledge -----------------------------------------------------------------
LEDGE_W = 3.0
LEDGE_Z = L.TRAY_Z0                   # its top face: the tray's underside lands here

# --- colour groove ----------------------------------------------------------------
GROOVE_D = 0.6                        # depth at BAND_H
GROOVE_LOW = 0.3                      # lower flank height (faces up)
GROOVE_UP = 0.9                       # upper flank height: tall enough to print
GROOVE_H = GROOVE_LOW + GROOVE_UP

# --- charger fence ------------------------------------------------------------------
FENCE_H = 8.0
POCKET_BACK_SLACK = 2.0               # free X behind the charger, at floor level
PORT_PLUG_ROOM_MIN = 40.0             # least free X in front of the ports
POCKET_X = M.CHARGER.port_to_inlet + 2 * P.CLR_FIT
POCKET_Y = M.CHARGER.port_face_width + 2 * P.CLR_FIT
POCKET_R = M.CHARGER.corner_r + P.CLR_FIT     # concentric with the charger's corner
FENCE_R = POCKET_R + P.WALL
FENCE_Y = POCKET_Y + 2 * P.WALL
CAVITY_FLOOR = RIM.at(P.FLOOR, WALL_H)        # (sx, sy, r) of the cavity at the floor
CAVITY_MIN_X, CAVITY_MAX_X = -CAVITY_FLOOR[0] / 2, CAVITY_FLOOR[0] / 2
POCKET_MIN_X = CAVITY_MIN_X + POCKET_BACK_SLACK
POCKET_MAX_X = POCKET_MIN_X + POCKET_X        # the charger's port face
FENCE_MIN_X = CAVITY_MIN_X + P.CLR_FIT
FENCE_MAX_X = POCKET_MAX_X + P.WALL
PORT_PLUG_ROOM = CAVITY_MAX_X - POCKET_MAX_X
FENCE_MARGIN_Y = (CAVITY_FLOOR[1] - FENCE_Y) / 2

# --- cord port (as v1) --------------------------------------------------------------
CORD_W = M.CORD_END.width + 2.0
CORD_H = M.CORD_END.height + 2.0
CORD_Z0 = max(P.FLOOR + M.CHARGER.inlet_center_z - CORD_H / 2, P.FLOOR + 1.0)
SUPPORTED_CEILINGS = ("cord port",)

# --- escape ports --------------------------------------------------------------------
ESCAPE_L = 14.0                        # along Y
ESCAPE_H = 8.0                         # along Z; the ends are full rounds
ESCAPE_Z0 = P.BAND_H + GROOVE_UP + 1.5
ESCAPE_ZC = ESCAPE_Z0 + ESCAPE_H / 2
_ESC = RIM.at(ESCAPE_ZC)
ESCAPE_FLAT_Y = _ESC[1] / 2 - _ESC[2]  # where the -X wall's flat meets its corner arc
ESCAPE_Y = (FENCE_Y / 2 + ESCAPE_FLAT_Y) / 2

# --- floor ---------------------------------------------------------------------------
TIE_D = 4.0
TIE_PITCH = 24.0
TIE_MARGIN = 6.0
FOOT_R = 5.0
FOOT_RECESS_D = 0.6
FOOT_INSET = 12.0
BED_FACE = RIM.at(0.0, taper.bed_chamfer_inset())
FOOT_CENTRES = [(sx * (BED_FACE[0] / 2 - FOOT_INSET), sy * (BED_FACE[1] / 2 - FOOT_INSET))
                for sx in (-1, 1) for sy in (-1, 1)]
_OUTSIDE_X = -RIM.sx / 2 - 5.0         # -X wall cutters start out here


def _grid_axis(lo: float, hi: float, pitch: float) -> list[float]:
    n = int((hi - lo) // pitch)
    start = (lo + hi - n * pitch) / 2
    return [start + i * pitch for i in range(n + 1)]


def _inside_rounded(x, y, sx, sy, r, margin) -> bool:
    hx, hy, rr = sx / 2 - margin, sy / 2 - margin, max(r - margin, 0.0)
    if abs(x) > hx or abs(y) > hy:
        return False
    dx, dy = abs(x) - (hx - rr), abs(y) - (hy - rr)
    return not (dx > 0 and dy > 0) or math.hypot(dx, dy) <= rr


def _tie_grid() -> list[tuple[float, float]]:
    """Tie-down holes on the free floor in front of the fence, clear of the
    walls and the foot recesses."""
    sx, sy, r = CAVITY_FLOOR
    margin = TIE_MARGIN + TIE_D / 2
    xs = _grid_axis(FENCE_MAX_X + margin, CAVITY_MAX_X - margin, TIE_PITCH)
    ys = _grid_axis(-sy / 2 + margin, sy / 2 - margin, TIE_PITCH)
    return [(x, y) for x in xs for y in ys
            if _inside_rounded(x, y, sx, sy, r, margin)
            and all(math.hypot(x - fx, y - fy) > FOOT_R + TIE_D / 2 + 1.0
                    for fx, fy in FOOT_CENTRES)]


TIE_HOLES = _tie_grid()


def tray_seat() -> Location:
    """Moves the tray (its own coordinates) onto the ledge."""
    return Pos(0, 0, L.TRAY_Z0)


def _outer() -> Part:
    foot = loft([RIM.section(0.0, taper.bed_chamfer_inset()), RIM.section(P.CHAMFER)])
    return foot + RIM.solid(P.CHAMFER, BASE_H)


def _ledge() -> Part:
    z0 = LEDGE_Z - LEDGE_W
    band = RIM.solid(z0, LEDGE_Z, inset=WALL_H - 0.05)       # a hair into the wall
    opening = loft([RIM.section(z0 - 0.01, WALL_H - 0.1),
                    RIM.section(LEDGE_Z + 0.01, WALL_H + LEDGE_W)])
    return band - opening


def _fence() -> Part:
    fence = Pos(FENCE_MIN_X, 0, 0) * Box(FENCE_MAX_X - FENCE_MIN_X, FENCE_Y,
                                         P.FLOOR + FENCE_H, align=_END_LO)
    fence = fillet(fence.edges().filter_by(Axis.Z).group_by(Axis.X)[-1], FENCE_R)
    # the pocket, open toward -X so the end wall closes it
    pocket = Pos(FENCE_MIN_X - 1.0, 0, P.FLOOR) * Box(
        POCKET_MAX_X - FENCE_MIN_X + 1.0, POCKET_Y, FENCE_H + 1.0, align=_END_LO)
    pocket = fillet(pocket.edges().filter_by(Axis.Z).group_by(Axis.X)[-1], POCKET_R)
    return fence - pocket


def _cord_cutter() -> Part:
    return Pos(_OUTSIDE_X, 0, CORD_Z0) * Box(CAVITY_MIN_X + 1.0 - _OUTSIDE_X,
                                             CORD_W, CORD_H, align=_END_LO)


def _escape_cutters() -> Part:
    cut = None
    for s in (-1, 1):
        slot = Plane.YZ.offset(_OUTSIDE_X) * Pos(s * ESCAPE_Y, ESCAPE_ZC) * \
            SlotCenterToCenter(ESCAPE_L - ESCAPE_H, ESCAPE_H)
        c = extrude(slot, amount=CAVITY_MIN_X + 1.0 - _OUTSIDE_X)
        cut = c if cut is None else cut + c
    return cut


def _groove_cutter() -> Part:
    z0, z1 = P.BAND_H - GROOVE_LOW, P.BAND_H + GROOVE_UP
    core = loft([RIM.section(z0), RIM.section(P.BAND_H, GROOVE_D), RIM.section(z1)],
                ruled=True)
    return RIM.solid(z0, z1, inset=-2.0) - core


def _floor_cutters() -> Part:
    cut = None
    for x, y in TIE_HOLES:
        c = Pos(x, y, -1.0) * Cylinder(TIE_D / 2, P.FLOOR + 2.0, align=_MIN)
        cut = c if cut is None else cut + c
    for x, y in FOOT_CENTRES:
        cut += Pos(x, y, 0) * Cylinder(FOOT_R, FOOT_RECESS_D, align=_MIN)
    return cut


def build_base() -> Part:
    part = _outer() - RIM.solid(P.FLOOR, BASE_H + 1.0, inset=WALL_H)
    part += _ledge()
    part += _fence()
    part -= _cord_cutter()
    part -= _escape_cutters()
    part -= _groove_cutter()
    part -= _floor_cutters()
    part -= H.base_relief()
    part += H.base_knuckles()
    return part
```

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest -q`
Expected: all pass. (The v1 tray still builds from its `V1_*` values; nothing reads it together with the new base until Task 7.)

- [ ] **Step 5: Commit**

```bash
git add src/dock/base.py tests/test_base.py
git commit -m "Base: tapered two-tone shell, tray ledge, rounded fence, oval escape ports, hinge pins"
```

---

### Task 6: Tray with fixed dividers; retire the v1 leftovers

**Files:**
- Rewrite: `src/dock/tray.py`, `tests/test_tray.py`, `scripts/export_all.py`
- Delete: `src/dock/divider.py`, `tests/test_divider.py`
- Modify: `src/dock/params.py` (drop the `V1_*` block and `CLR_RAIL`), `tests/test_params.py`

**Interfaces:**
- Consumes: `layout.BAYS`, `TRAY_OUTLINE`, `TRAY_H`, `INNER_FILLET_R`, `FLOOR_FILLET_R`, `cutouts()`; `taper.*`.
- Produces: `tray.build_tray() -> Part`, `tray.WALL_H`, `TRAY_H`, `TRAY_X`, `TRAY_Y`, `TOP_ROUND_R` (0.8), `SLOT_W`, `SLOT_H`, `SLOT_TOP_DROP`, `PARTITION_X`.

- [ ] **Step 1: Write the new tests**

```bash
git rm src/dock/divider.py tests/test_divider.py
```

Replace `tests/test_tray.py` with:

```python
"""Tray tests: measured on the built solid."""
import math
from functools import lru_cache

from build123d import Align, Axis, Box, Pos

from dock import layout as L, params, taper, tray
from printability import steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@lru_cache(maxsize=None)
def _tray():
    return tray.build_tray()


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=_CTR)


def _solid(probe):
    return (probe & _tray()).volume >= probe.volume * (1 - 1e-4)


def _clear(probe):
    return (probe & _tray()).volume < probe.volume * 1e-6


def _slab(z):
    return _tray() & (Pos(0, 0, z) * Box(400, 400, 2e-3, align=_CTR))


def test_tray_is_one_valid_solid_on_the_bed_and_fits_it():
    p = _tray()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and bb.size.X <= params.BED_X and bb.size.Y <= params.BED_Y


def test_the_outer_walls_lean_at_the_draft_up_to_the_layout_outline():
    z0, z1 = 10.0, 35.0
    lean = (_slab(z0).bounding_box().min.Y - _slab(z1).bounding_box().min.Y) / (z1 - z0)
    assert math.isclose(lean, taper.TAN, abs_tol=1e-3)
    bb = _slab(L.TRAY_H - 0.01).bounding_box()
    assert math.isclose(bb.size.X, L.TRAY_OUTLINE.at(L.TRAY_H - 0.01)[0], abs_tol=0.02)


def test_the_outer_wall_is_thin_wall_thick_square_to_the_slope():
    b = L.BAYS["roam"]
    z = 20.0
    y_out = -L.TRAY_OUTLINE.at(z)[1] / 2
    w = tray.WALL_H
    assert _solid(_box(b.cx, y_out + w / 2, z, 4, w - 0.1, 0.02))
    assert _clear(_box(b.cx, y_out + w + 0.1, z, 4, 0.1, 0.02))


def test_the_plate_is_tray_plate_thick():
    b = L.BAYS["trackr"]
    x = b.x0 + 20.0
    assert _solid(_box(x, b.cy, params.TRAY_PLATE / 2, 2, 2, params.TRAY_PLATE - 0.04))
    assert _clear(_box(x, b.cy, params.TRAY_PLATE + 5.0, 2, 2, 5.0))


def test_every_device_lies_in_its_bay_clear_of_the_tray():
    for name, dev in L.DEVICES.items():
        x0, x1, y0, y1 = L.device_footprint(name)
        box = Pos((x0 + x1) / 2, (y0 + y1) / 2, params.TRAY_PLATE + 0.01) * Box(
            x1 - x0, y1 - y0, dev.thickness, align=_MIN)
        assert _clear(box), name


def test_the_bays_are_open_to_the_rim():
    for b in L.BAYS.values():
        assert _clear(_box(b.cx, b.cy, (L.TRAY_H + params.TRAY_PLATE) / 2 + 3, 10, 10, L.TRAY_H - params.TRAY_PLATE - 6))


def test_the_internal_walls_are_fixed_and_wall_thick():
    part_x = tray.PARTITION_X
    assert _solid(_box(part_x, 40.0, 25.0, params.WALL - 0.05, 5, 5))
    for y0, y1 in ((L.BAYS["spare"].y1, L.BAYS["trackr"].y0), (L.BAYS["trackr"].y1, L.BAYS["ion"].y0)):
        assert math.isclose(y1 - y0, params.WALL)
        assert _solid(_box(L.BAYS["trackr"].cx, (y0 + y1) / 2, 25.0, 20, params.WALL - 0.05, 5))


def test_inside_corners_are_filleted_about_r6():
    # where the spare/trackr divider meets the partition, on the trackr side
    x = L.BAYS["trackr"].x0
    y = L.BAYS["trackr"].y0
    r = L.INNER_FILLET_R
    assert _solid(_box(x + 0.25 * r, y + 0.25 * r, 20.0, 0.1, 0.1, 0.1))
    assert _clear(_box(x + 0.35 * r, y + 0.35 * r, 20.0, 0.1, 0.1, 0.1))


def test_walls_meet_the_floor_in_an_r3_fillet():
    x = L.BAYS["trackr"].x0            # the partition's +X face
    y = L.BAYS["trackr"].cy
    r = L.FLOOR_FILLET_R
    z = params.TRAY_PLATE
    assert _solid(_box(x + 0.25 * r, y, z + 0.25 * r, 0.1, 0.1, 0.1))
    assert _clear(_box(x + 0.35 * r, y, z + 0.35 * r, 0.1, 0.1, 0.1))


def test_the_internal_wall_tops_are_rounded():
    x = tray.PARTITION_X + params.WALL / 2 - 0.1
    assert _clear(_box(x, 40.0, L.TRAY_H - 0.1, 0.1, 1, 0.1))
    assert _solid(_box(tray.PARTITION_X, 40.0, L.TRAY_H - 0.1, 0.1, 1, 0.1))


def test_six_cable_cutouts_through_the_plate_where_the_layout_puts_them():
    bottom = _tray().faces().sort_by(Axis.Z)[0]
    holes = sorted((w.bounding_box().center().X, w.bounding_box().center().Y) for w in bottom.inner_wires())
    want = sorted((c[1], c[2]) for c in L.cutouts())
    assert len(holes) == len(want) == 6
    for (hx, hy), (wx, wy) in zip(holes, want):
        assert math.isclose(hx, wx, abs_tol=0.01) and math.isclose(hy, wy, abs_tol=0.01)


def test_the_finger_slot_goes_through_the_partition_under_a_45_degree_arch():
    top = L.TRAY_H - tray.SLOT_TOP_DROP
    x = tray.PARTITION_X
    assert _clear(_box(x, 0, top - tray.SLOT_H / 2, params.WALL + 0.2, 4, 4))
    assert _clear(_box(x, 0, top - 0.5, params.WALL + 0.2, 0.2, 0.2))
    assert _solid(_box(x, tray.SLOT_W / 2 - 0.5, top - 0.5, params.WALL - 0.1, 0.2, 0.2))


def test_the_tray_prints_with_no_overhang():
    assert steep_faces(_tray()) == []
```

In `tests/test_params.py`, add at the end of `test_design_rules_match_spec`:

```python
    # removed with the removable dividers and the last v1 module
    assert not hasattr(params, "CLR_RAIL")
    for name in ("V1_WALL", "V1_FLOOR", "V1_CORNER_R", "V1_TRAY_PLATE"):
        assert not hasattr(params, name)
```

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest tests/test_tray.py tests/test_params.py -q`
Expected: failures (v1 tray is not tapered; `CLR_RAIL` still in params). Collection may also fail because the v1 tray imports `divider`; that is expected.

- [ ] **Step 3: Write `src/dock/tray.py`**

```python
"""Tray: four bays for devices lying face up, in a tapered shell that
nests in the base.

The bays are laid out in layout.py -- ROAM on the left, spare/TRACKR/Ion
stacked on the right -- and each is cut as its own void: a loft from the bay
floor up past the rim, leaning out at the draft on the sides that lie on the
tray's outer wall and standing vertical on the internal ones.  The material
left between the voids is the partition and the two dividers, fixed and
printed with the tray.  Each void's corners are rounded before it is cut:
INNER_FILLET_R where it meets an internal wall, the tray's own corner radius
(less the wall) where it meets two outer walls, so the shell keeps its
thickness through those corners.  Its floor edges are rounded
FLOOR_FILLET_R, and once all four are cut the tops of the walls are rounded
TOP_ROUND_R.  All of these face up or sideways, so they print.

The tray is lifted out by the partition, through a finger slot with a 45
degree pointed head.  Cable cutouts go through the plate where layout.py
puts them.

Tray coordinates: XY centred, plate underside at Z = 0.  Printed plate-down,
bays up; nothing overhangs.
"""
from build123d import Align, Axis, Box, Part, Plane, Polygon, Pos, extrude, fillet, loft

from dock import layout as L
from dock import params as P
from dock import taper

WALL_H = taper.horiz(P.THIN_WALL)      # the outer wall, measured horizontally
TRAY_H = L.TRAY_H
TRAY_X, TRAY_Y = L.TRAY_OUTLINE.sx, L.TRAY_OUTLINE.sy     # at the rim
TOP_ROUND_R = 0.8     # a full round of a WALL-thick top would leave no face to fillet
SLOT_W = 25.0
SLOT_H = 15.0
SLOT_TOP_DROP = 5.0   # slot apex below the rim
PARTITION_X = L.BAYS["roam"].x1 + P.WALL / 2
_OVER = 5.0           # voids run this far past the rim
_CORNER_SIDES = {"--": (0, 2), "+-": (1, 2), "++": (1, 3), "-+": (0, 3)}


def _void_radii(b: L.Bay, z: float) -> dict[str, float]:
    outer_r = L.TRAY_OUTLINE.at(z, WALL_H)[2]
    return {k: outer_r if (b.sloped[i] and b.sloped[j]) else L.INNER_FILLET_R
            for k, (i, j) in _CORNER_SIDES.items()}


def _bay_void(b: L.Bay) -> Part:
    z0, z1 = P.TRAY_PLATE, TRAY_H + _OVER
    g = [(z1 - z0) * taper.TAN if s else 0.0 for s in b.sloped]
    lo = taper.corner_rect(b.x0, b.x1, b.y0, b.y1, _void_radii(b, z0), z0)
    hi = taper.corner_rect(b.x0 - g[0], b.x1 + g[1], b.y0 - g[2], b.y1 + g[3],
                           _void_radii(b, z1), z1)
    void = loft([lo, hi])
    return fillet(void.faces().sort_by(Axis.Z)[0].edges(), L.FLOOR_FILLET_R)


def _finger_slot() -> Part:
    top = TRAY_H - SLOT_TOP_DROP
    bot = top - SLOT_H
    shoulder = top - SLOT_W / 2          # 45-degree head
    pts = [(-SLOT_W / 2, bot), (SLOT_W / 2, bot), (SLOT_W / 2, shoulder),
           (0.0, top), (-SLOT_W / 2, shoulder)]
    face = Plane.YZ.offset(PARTITION_X - P.WALL) * Polygon(*pts, align=None)
    return extrude(face, amount=2 * P.WALL)


def build_tray() -> Part:
    part = L.TRAY_OUTLINE.solid(P.CHAMFER, TRAY_H) + loft(
        [L.TRAY_OUTLINE.section(0.0, taper.bed_chamfer_inset()),
         L.TRAY_OUTLINE.section(P.CHAMFER)])
    for b in L.BAYS.values():
        part -= _bay_void(b)
    top = part.faces().sort_by(Axis.Z)[-1]
    part = fillet([e for w in top.inner_wires() for e in w.edges()], TOP_ROUND_R)
    part -= _finger_slot()
    for _, cx, cy, sx, sy in L.cutouts():
        part -= Pos(cx, cy, -1.0) * Box(sx, sy, P.TRAY_PLATE + 2.0,
                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part
```

- [ ] **Step 4: Drop the v1 leftovers**

In `src/dock/params.py`, delete the `# v1 values ...` comment block, the four `V1_*` lines and the `CLR_RAIL` line. Check nothing reads them any more:

Run: `grep -rnE "V1_|CLR_RAIL|import divider|divider\." src scripts`
Expected: no output. (`tests/test_params.py` still names `CLR_RAIL` and `V1_*`, in the assertions that they are gone.)

- [ ] **Step 5: Final `scripts/export_all.py`**

```python
"""Export every registered part into out/, then report the numbers worth
checking before a print: what each part measures, and how much room is left
around the charger inside the base."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import base
from dock import coupon
from dock import hinge
from dock import layout
from dock import lid
from dock import tray


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


def _hinge_coupon_base() -> Part:
    return coupon.build_hinge_coupon()[0]


def _hinge_coupon_lid() -> Part:
    return coupon.build_hinge_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
    "hinge_coupon_base": _hinge_coupon_base,
    "hinge_coupon_lid": _hinge_coupon_lid,
    "base": base.build_base,
    "tray": tray.build_tray,
    "lid": lid.build_lid,
}


def build_report() -> str:
    """The derived sizes and clearances, in mm, read off the built parts.
    Every one of them moves on its own when a measurement or a design rule
    changes, so print them where they can be read before a long print."""
    lines = ["build report (mm, as printed)"]
    for name in ("base", "tray", "lid"):
        s = PARTS[name]().bounding_box().size
        lines.append(f"  {name:<5}{s.X:8.2f} x {s.Y:7.2f} x {s.Z:6.2f}")
    lines += [
        f"  charger fence: {base.FENCE_MARGIN_Y:.2f} free each side; port room "
        f"{base.PORT_PLUG_ROOM:.2f} (need {base.PORT_PLUG_ROOM_MIN:.2f})",
        f"  lid lip {layout.LIP_W:.2f} proud; hinge opens to {hinge.OPEN_DEG:.0f} deg",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
    print()
    print(build_report())
```

- [ ] **Step 6: Run the whole suite and the export**

Run: `uv run pytest -q && uv run python scripts/export_all.py`
Expected: all pass; the report shows base 242.9 × 186.8 × 85.2, tray 237.7 × 172.5 × 39.2, lid 249.5 × 192.3 × 13.5 (the base's height and depth include the hinge cheeks).

- [ ] **Step 7: Commit**

```bash
git add -A src scripts tests
git commit -m "Tray: tapered shell with fixed, filleted dividers; retire the removable divider"
```

---

### Task 7: Assembly

**Files:**
- Create: `tests/test_assembly.py`

**Interfaces:**
- Consumes: `base.build_base()`, `base.tray_seat()`, `tray.build_tray()`, `lid.build_lid()`, `lid.lid_seat(deg)`, `hinge.OPEN_DEG`, `hinge.BORE_R`, `layout.*`.

These check the parts against each other: the tray on the ledge, the lid on the rim and swinging, the heel stop, the snap, and the cable drop. They should pass straight away if Tasks 4-6 are right; any failure is a real fit problem to fix in the part, not in the test.

- [ ] **Step 1: Write the tests**

```python
"""The parts together: tray in the base, lid on the rim, lid swinging."""
import math
from functools import lru_cache

from build123d import Align, Box, Pos

from dock import base, hinge as H, layout as L, lid, params, taper, tray

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@lru_cache(maxsize=None)
def _base():
    return base.build_base()


@lru_cache(maxsize=None)
def _tray():
    return base.tray_seat() * tray.build_tray()


@lru_cache(maxsize=None)
def _printed_lid():
    return lid.build_lid()


def _lid(deg=0.0):
    return lid.lid_seat(deg) * _printed_lid()


def _hit(a, b):
    return (a & b).volume


def test_the_tray_seats_in_the_base_on_the_ledge():
    assert _hit(_tray(), _base()) < 1e-3
    assert _hit(Pos(0, 0, -0.2) * _tray(), _base()) > 1e-3


def test_the_tray_rim_sits_just_below_the_base_rim():
    assert math.isclose(L.BASE_H - _tray().bounding_box().max.Z, L.TRAY_SINK, abs_tol=0.01)


def test_the_closed_lid_rests_on_the_rim_clear_of_everything():
    assert _hit(_lid(), _base()) < 1e-3
    assert _hit(_lid(), _tray()) < 1e-3
    assert _hit(Pos(0, 0, -0.2) * _lid(), _base()) > 1e-3


def test_devices_on_the_seated_tray_clear_the_closed_lid():
    for name, dev in L.DEVICES.items():
        x0, x1, y0, y1 = L.device_footprint(name)
        box = Pos((x0 + x1) / 2, (y0 + y1) / 2, L.TRAY_Z0 + params.TRAY_PLATE + 0.01) * Box(
            x1 - x0, y1 - y0, dev.thickness, align=_MIN)
        assert _hit(box, _lid()) < 1e-6, name
        assert _hit(box, _tray()) < 1e-6, name


def test_the_lid_swings_open_clear_of_the_base_and_tray():
    for deg in (5, 20, 40, 60, 80, 100, H.OPEN_DEG - 2):
        assert _hit(_lid(deg), _base()) < 1e-3, deg
        assert _hit(_lid(deg), _tray()) < 1e-3, deg


def test_the_heel_stops_the_lid_just_past_open():
    assert _hit(_lid(H.OPEN_DEG + 3), _base()) > 1e-3


def test_a_closed_lid_lifted_catches_on_the_pins():
    assert _hit(Pos(0, 0, 1.0) * _lid(), _base()) > 1e-3


def test_at_full_open_the_lid_lifts_off_along_the_wall_over_the_snap():
    t = math.radians(params.TAPER_DEG)
    def lifted(s):
        return Pos(0, s * math.sin(t), s * math.cos(t)) * _lid(H.OPEN_DEG - 1)
    assert _hit(lifted(H.BORE_R), _base()) > 1e-3             # the neck snaps over the pin
    assert _hit(lifted(2 * H.BORE_R + 2.0), _base()) < 1e-3   # and then it is off


def test_the_assembled_dock_fits_the_bed_footprint():
    for part in (_base(), _tray(), _lid()):
        s = part.bounding_box().size
        assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_cables_drop_at_least_15_mm_clear_below_every_cutout():
    for _, cx, cy, sx, sy in L.cutouts():
        col = Pos(cx, cy, L.TRAY_Z0 - 15.0) * Box(sx - 0.02, sy - 0.02, 15.0 - 0.01, align=_MIN)
        assert _hit(col, _base()) < 1e-3, (cx, cy)
```

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_assembly.py -q`
Expected: 10 passed. If one fails, stop and report which, with the numbers; do not loosen a test to pass it.

- [ ] **Step 3: Run the whole suite**

Run: `uv run pytest -q`
Expected: all pass (95 at the time of planning).

- [ ] **Step 4: Commit**

```bash
git add tests/test_assembly.py
git commit -m "Assembly tests: tray seat, lid swing and stop, hinge snap, cable drop"
```

---

### Task 8: Docs, efficiency check and export

**Files:**
- Modify: `docs/printing.md`, `CLAUDE.md`, `docs/superpowers/specs/2026-09-23-tapered-dock-design.md` (status line)

- [ ] **Step 1: Export and slice**

Run: `uv run python scripts/export_all.py && uv run python scripts/slice_report.py && uv run python scripts/slice_report.py --layer 0.28`
Expected at 0.20: a v2 set of about 9 h 53 m / 412 g, `time -29 %, filament -29 %`. **If either is worse than -25 %, stop and report the table to the user; do not change geometry to chase it.**

- [ ] **Step 2: Rewrite `docs/printing.md`**

Replace the file with the following, then put the two measured totals from Step 1 into its "Efficiency" section if they differ from the planning numbers:

```markdown
# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (open the .stl files; Orca rejects generic 3MF), installed as a Flatpak.

    flatpak run io.github.Snapmaker.Snapmaker_Orca

Printer: Snapmaker U1. Material: PETG for the final set (fit-checking in PLA
is fine). Profile: 0.4 mm nozzle, 0.2 mm layers; 0.28 mm Extra Draft is an
option for the base and lid, see below.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| hinge_coupon_base, hinge_coupon_lid | as exported | 3 | 15 % | none |
| tray | as exported: plate on the bed, bays up | 3 | 15 % | none |
| base | as exported: open top up | 3 | 15 % | the cord port ceiling only (26 mm); paint-on or "support on build plate only" |
| lid | as exported: top face down, hinge hooks up | 3 | 15 % | none |

There are no dividers to print: the tray's dividers are fixed and print with it.

## Efficiency

`uv run python scripts/slice_report.py` slices the exported base, tray and
lid headlessly with these settings and prints time and grams next to the v1
prototype (`--layer 0.28` for the draft profile). Measured when the design
was planned, 0.20 mm PETG: v1 set 14 h 00 m / 582 g, this set 9 h 53 m /
412 g (-29 %). Re-run it after any change to params.py and before a
reprint.

The base and lid can also print at 0.28 mm Extra Draft for a little more
time saved; the tray's cable cutouts and fillets look better at 0.20.

## Two-tone base

The base is two colours like the Trek CHRGtime: a dark foot band and a light
body. The colour line is the V groove round the foot at `BAND_H` (8 mm);
it is 1.2 mm tall, so any layer inside it works at 0.20 or 0.28:

1. In Orca, load the dark filament in one toolhead and the light in another,
   and set the base's object filament to the dark one.
2. Add a filament change at a layer inside the groove -- 8.0 mm at 0.20 --
   to the light filament (right-click the layer slider, "Change filament").
3. Turn the prime/wipe tower off for this plate (Others > Prime tower): one
   change on a toolchanger does not need it, and the tower would cost more
   than the whole change.

Print the lid and the tray in the dark colour.

## Geometry notes

Every outer face leans 15 degrees (the CHRGtime's angle), from the lid top
down to the foot; the corners run from R30 at the rim to about R8 at the
bed. The base walls lean outward as they rise, well inside 45 degrees, so
the whole shell prints unsupported; the only supported ceiling is the AC
cord port's flat top (`base.SUPPORTED_CEILINGS`). The escape ports' heads,
the foot recesses and the hinge pins' 3 mm flats are short bridges.

The charger (Anker A2154) stands in a U fence backed onto the -X end wall;
its corners follow the charger's rounded edges (`CHARGER.corner_r`). The
mains cord plugs in from outside through the cord port. Two oval escape
ports, one each side of the charger in the same wall, let a cable out to
charge something outside the dock.

The tray rests on a ledge ring 0.3 mm below the rim, so the lid lands on the
base. Lift it out by the finger slot in the centre partition. The cable
cutouts at the bays' outer ends drop past the leaning base wall: the cable
falls clear for at least 15 mm, then follows the wall down.

## Hinge

The lid hinges on the +Y long side at two stations. The base carries the
pins, the lid the hooks. To fit the lid: open it to full (about 110
degrees, where the heel tab in the middle rests on the base's back wall),
line the hooks up over the pins, and push it down along the wall until the
hooks snap on. To take it off, open it fully and pull it up along the wall.
A closed lid lifted straight up stays on.

Print the hinge coupon first: it is one station on a short stretch of wall
and lid. If the hook will not snap on, or falls off, change `SNAP` in
`src/dock/hinge.py`; if the hinge binds, raise `BORE_CLR`. Then re-export.

## Print order and measurement cycle

1. **coupons** -- the clearance coupon and the hinge coupon, in the final
   material. Set `CLR_FIT` (params.py) and `SNAP` / `BORE_CLR` (hinge.py).
2. **measurements** -- fill in `src/dock/measurements.py` per
   `docs/measuring.md`; `CHARGER.corner_r` is new.
3. **tray** -- check each device seats in its bay and its cable plugs in
   cleanly through the cutout.
4. **base** -- check the charger drops into the fence and the tray seats on
   the ledge.
5. **lid** -- check it snaps on at full open, swings shut flush with the
   rim, and clears every device.

Re-run `uv run python scripts/export_all.py` after any parameter change, and
`uv run pytest` before reprinting.

## Flatpak note

The Snapmaker Orca Flatpak has no host filesystem access by default, so
`flatpak run ... out/part.stl` opens the app but reports "no geometry data".
Either grant it this folder once:

    flatpak override --user --filesystem=$PWD io.github.Snapmaker.Snapmaker_Orca

or launch it without arguments and use File > Import (the file portal).

The GUI also changes its working directory after launch, so pass ABSOLUTE
paths on the command line (`$PWD/out/part.stl`); relative paths fail with
"no geometry data".

To verify every part loads in Orca without opening the GUI:

    scripts/orca_check.sh

It writes Orca project files to out/orca/<part>.3mf, which File > Open
Project in Orca accepts directly.
```

- [ ] **Step 3: Rewrite `CLAUDE.md`**

```markdown
# Charging dock (build123d)

Parametric 3D-print models for a cycling-electronics charging dock: a tapered base, a tray with fixed dividers, and a hinged lid, plus clearance and hinge calibration coupons. Spec and plan live in docs/superpowers/; the current design is specs/2026-09-23-tapered-dock-design.md. The printed v1 prototype is tagged `v1-prototype`.

## Toolchain
- Python 3.12 via uv only (system Python is 3.14; build123d has no wheels for it): `uv venv --python 3.12 && uv pip install -e ".[dev]"`, then `uv run pytest` / `uv run python scripts/export_all.py`.
- Slice in Snapmaker Orca (Flatpak io.github.Snapmaker.Snapmaker_Orca) for the Snapmaker U1, PETG. See docs/printing.md.
- `uv run python scripts/slice_report.py [--layer 0.28]` slices out/base,tray,lid headlessly and compares time and grams with v1 (not part of pytest; minutes). The design target is at least 25 % below v1 in both.
- build123d 0.12: `part.is_valid` is a property; `ShapeList.sort_by(Axis.Z)`, not a lambda.

## Conventions
- All dimensions in mm; design rules in src/dock/params.py, caliper inputs in src/dock/measurements.py (values marked NOMINAL are guesses until measured; see docs/measuring.md).
- Every outer face shares one 15 degree draft: build drafted shapes from `taper.Outline` (layout.RIM, layout.TRAY_OUTLINE), never by hand, so corners stay concentric. Where things go is in layout.py (numbers only).
- One `build_*()` per printed part, print-bed face at Z=0, algebra API (`Box - Pos(...) * Box`). XY is centred and shared by every part.
- Tests must measure the built solid (faces, wires, bounding boxes, intersections, probes), not restate constants. Every exported part is checked as a single valid solid on the bed in tests/test_parts.py; overhangs through tests/printability.py.
- Chamfers not fillets on downward edges; no overhang past 45 degrees; short bridges (<= 20 mm) are allowlisted in the overhang tests.
- out/ is gitignored; never commit exports.
```

- [ ] **Step 4: Mark the spec implemented**

In the spec, change `Status: approved in chat, sections 1–3` to `Status: implemented on branch tapered-dock (plan docs/superpowers/plans/2026-09-24-tapered-dock.md)`.

- [ ] **Step 5: Check Orca loads every part**

Run: `scripts/orca_check.sh`
Expected: every out/*.stl loads (result return_code 0).

- [ ] **Step 6: Commit**

```bash
git add docs CLAUDE.md
git commit -m "Docs: printing the tapered dock -- two-tone base, hinge, efficiency report"
```

---

## Self-review against the spec

- Exterior (15° true draft, R30→R8, two-tone band + groove, lid slope + lip, no skirt/plinth/notches, bed limit): Tasks 2, 4, 5 (`layout.RIM`, `LIP_W` bed rule, groove and corner tests).
- Tray (tapered THIN_WALL shell, 1.2 plate, bay clearances, cutouts incl. 3 under the Ion, fixed WALL dividers, R6 / R3 / top rounding, finger slot): Tasks 2, 6.
- Base (single WALL shell, 1.2 floor, ledge, fence with charger-corner fillets and no fingernail notch, cord port, two oval escape ports, tie grid, feet, plain rim, cable drop ≥ 15 mm): Tasks 5, 7.
- Hinge (axis, cheeks/pin with flat, relief discs, hooks with teardrop bore and snap neck, mouth for lift-off along the wall at full open, captive when closed, heel stop at X = 0, coupon): Tasks 3, 4, 7.
- Removed parts (divider, rails, CLR_RAIL, plinth, rebate, notches): Tasks 4-6.
- Efficiency (slice report, baseline, ≥ 25 % target, 0.28 option, prime tower note): Tasks 1, 8.
- Docs (printing, measuring corner_r, CLAUDE.md): Tasks 2, 8.
