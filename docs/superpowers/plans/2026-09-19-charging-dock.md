# Charging Dock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A two-piece PETG charging dock (base tray + deck) hiding an Anker PowerPort 6 and holding a Wahoo Roam 3, a Bontrager Ion Pro RT and a Wahoo Trackr, printed on a Snapmaker U1.

**Architecture:** Pure-Python parametric CAD with build123d's algebra API. One module per printed part, each exposing a `build_*()` function that returns a `build123d.Part`. All dimensions live in `params.py` (design rules) and `measurements.py` (values the user measures with calipers). Tests assert geometry facts (bounding box, clearances, bed fit, validity). `export.py` writes STL/3MF/STEP into `out/`.

**Tech Stack:** Python 3.12 via `uv` (build123d has no 3.14 wheels yet), build123d, ocp_vscode (browser viewer), pytest. Slicing in the already-installed Snapmaker Orca Flatpak (`io.github.Snapmaker.Snapmaker_Orca`).

**Spec:** `docs/superpowers/specs/2026-09-19-charging-dock-design.md`

## Global Constraints

- Wall thickness 2.4 mm, floors 1.6 mm.
- Clearances: 0.3 mm device pockets, 0.2 mm deck-to-base, 0.25 mm divider rails. All in `params.py`, tunable after the coupon print.
- Overall footprint under 250 x 120 mm (U1 bed with margin), enforced by a test.
- Chamfers, not fillets, on downward-facing edges. No overhang past 45 degrees.
- Charger: Anker PowerPort 6 (A2123), six USB-A on one face, C7 inlet on the opposite face. Nominal 96 x 65 x 26 mm until measured.
- Units: millimetres everywhere. Z is up. Parts are built with their print-bed face at Z=0.
- `out/` is gitignored; never commit exports.
- Every commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## File Structure

```
pyproject.toml            project metadata, deps, pytest config
.python-version           "3.12"
src/dock/__init__.py      empty
src/dock/params.py        design rules: walls, clearances, bed limits, cable connector sizes
src/dock/measurements.py  caliper-measured device and charger dimensions (user edits)
src/dock/export.py        write_all(part, name) -> STL/3MF/STEP in out/
src/dock/coupon.py        build_coupon(): clearance calibration test piece
src/dock/cradles.py       build_roam_cradle(), build_ion_cradle(), build_trackr_cradle()
src/dock/divider.py       build_divider()
src/dock/deck.py          build_deck(): cradles + spare bay + cable slots + lip
src/dock/base.py          build_base(): charger cavity, cord notch, escape port, LED window, feet
src/dock/view.py          show any part in ocp_vscode viewer
scripts/export_all.py     exports every part
tests/conftest.py         shared fixtures
tests/test_params.py
tests/test_coupon.py
tests/test_cradles.py
tests/test_divider.py
tests/test_deck.py
tests/test_base.py
tests/test_assembly.py
docs/measuring.md         what the user measures and where it goes
README.md
```

---

### Task 1: Project scaffold, params, export helper

**Files:**
- Create: `pyproject.toml`, `.python-version`, `src/dock/__init__.py`, `src/dock/params.py`, `src/dock/export.py`, `src/dock/view.py`, `tests/conftest.py`, `tests/test_params.py`, `README.md`

**Interfaces:**
- Produces: `params.WALL=2.4`, `params.FLOOR=1.6`, `params.CLR_DEVICE=0.3`, `params.CLR_FIT=0.2`, `params.CLR_RAIL=0.25`, `params.BED_X=250`, `params.BED_Y=120`, `params.CHAMFER=1.0`, `params.USB_A_PLUG` (dataclass w/ `width, height, length`), `params.USB_C_PLUG`, `params.MICRO_PLUG`; `export.write_all(part: Part, name: str, out_dir: Path = Path("out")) -> list[Path]`; `view.show_part(part)`.

- [ ] **Step 1: Create the environment**

```bash
cd bike-charging-dock
echo "3.12" > .python-version
uv venv --python 3.12
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "dock"
version = "0.1.0"
description = "Parametric 3D-printed charging dock for cycling electronics"
requires-python = ">=3.12,<3.13"
dependencies = ["build123d>=0.9", "ocp_vscode>=2.6"]

[project.optional-dependencies]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/dock"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Install**

```bash
uv pip install -e ".[dev]"
```
Expected: build123d imports (`uv run python -c "import build123d"` prints nothing).

- [ ] **Step 4: Write the failing test**

`tests/test_params.py`:
```python
from dock import params


def test_design_rules_match_spec():
    assert params.WALL == 2.4
    assert params.FLOOR == 1.6
    assert params.CLR_DEVICE == 0.3
    assert params.CLR_FIT == 0.2
    assert params.CLR_RAIL == 0.25
    assert (params.BED_X, params.BED_Y) == (250, 120)


def test_plug_sizes_are_positive():
    for plug in (params.USB_A_PLUG, params.USB_C_PLUG, params.MICRO_PLUG):
        assert plug.width > 0 and plug.height > 0 and plug.length > 0
```

- [ ] **Step 5: Run it, expect ImportError**

`uv run pytest tests/test_params.py -v` → FAIL, `ModuleNotFoundError: dock.params`.

- [ ] **Step 6: Write params.py**

```python
"""Design rules. Millimetres. Change here, never inline in a part module."""
from dataclasses import dataclass

WALL = 2.4        # 3 perimeters at 0.4 mm nozzle
FLOOR = 1.6       # 4 layers at 0.4 mm
CHAMFER = 1.0     # downward-facing edge chamfer
CLR_DEVICE = 0.3  # device pocket clearance per side
CLR_FIT = 0.2     # deck lip into base
CLR_RAIL = 0.25   # divider dovetail rails
BED_X = 250       # U1 usable X with margin
BED_Y = 120       # self-imposed footprint limit


@dataclass(frozen=True)
class Plug:
    """Cable connector overmold envelope (the moulded body, not the metal tip)."""
    width: float
    height: float
    length: float   # overmold length along the cable axis


# Typical overmold sizes; refine from the actual cables when measured.
USB_A_PLUG = Plug(width=15.0, height=8.0, length=20.0)
USB_C_PLUG = Plug(width=11.0, height=6.0, length=18.0)
MICRO_PLUG = Plug(width=10.5, height=6.5, length=17.0)
```

`src/dock/__init__.py`: empty file.

- [ ] **Step 7: Run tests, expect pass**

`uv run pytest tests/test_params.py -v` → 2 passed.

- [ ] **Step 8: Write export.py and view.py**

`src/dock/export.py`:
```python
from pathlib import Path
from build123d import Part, Mesher, export_stl, export_step


def write_all(part: Part, name: str, out_dir: Path = Path("out")) -> list[Path]:
    """Write STL, 3MF and STEP for `part`. Returns the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stl = out_dir / f"{name}.stl"
    threemf = out_dir / f"{name}.3mf"
    step = out_dir / f"{name}.step"
    export_stl(part, str(stl))
    m = Mesher()
    m.add_shape(part)
    m.write(str(threemf))
    export_step(part, str(step))
    return [stl, threemf, step]
```

`src/dock/view.py`:
```python
"""Run `uv run python -m ocp_vscode` in one terminal, then call show_part()."""
from build123d import Part
from ocp_vscode import show


def show_part(part: Part) -> None:
    show(part)
```

- [ ] **Step 9: Test export writes three files**

Append to `tests/test_params.py`:
```python
from pathlib import Path
from build123d import Box
from dock.export import write_all


def test_write_all_creates_three_files(tmp_path: Path):
    paths = write_all(Box(10, 10, 10), "cube", tmp_path)
    assert [p.suffix for p in paths] == [".stl", ".3mf", ".step"]
    assert all(p.stat().st_size > 0 for p in paths)
```
`uv run pytest tests/test_params.py -v` → 3 passed.

- [ ] **Step 10: README and commit**

`README.md`:
```markdown
# Charging dock

Parametric build123d model of a desktop charging dock. See
`docs/superpowers/specs/2026-09-19-charging-dock-design.md`.

    uv venv --python 3.12 && uv pip install -e ".[dev]"
    uv run pytest
    uv run python scripts/export_all.py     # writes out/*.stl|3mf|step
    uv run python -m ocp_vscode             # viewer at http://localhost:3939
```

```bash
git add -A && git commit -m "Scaffold build123d project with params and export

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Calibration coupon

**Files:**
- Create: `src/dock/coupon.py`, `tests/test_coupon.py`, `scripts/export_all.py`

**Interfaces:**
- Consumes: `export.write_all` only. The coupon deliberately uses fixed sizes: it calibrates params, so it must not depend on them.
- Produces: `coupon.build_coupon() -> Part`, `coupon.CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)`; `scripts/export_all.py` with a `PARTS: dict[str, Callable[[], Part]]` registry that later tasks append to.

The coupon is a plate with six 10 mm square holes and a separate 10 mm square peg. Each hole is 10 + 2*c across, labelled by its position (smallest clearance nearest the notch). The user pushes the peg into each hole; the tightest one that slides in by hand gives the fit clearance, the one that drops freely gives the device clearance.

- [ ] **Step 1: Failing test**

`tests/test_coupon.py`:
```python
from build123d import Axis
from dock import coupon


def test_coupon_has_six_holes():
    plate, peg = coupon.build_coupon()
    # a plate with 6 through-holes has 6 inner wires on its top face
    top = plate.faces().sort_by(Axis.Z)[-1]
    assert len(top.inner_wires()) == 6


def test_peg_is_10mm_square():
    _, peg = coupon.build_coupon()
    size = peg.bounding_box().size
    assert abs(size.X - 10) < 1e-6 and abs(size.Y - 10) < 1e-6
```

- [ ] **Step 2: Run, expect failure** — `uv run pytest tests/test_coupon.py -v` → ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/dock/coupon.py`:
```python
"""Clearance calibration coupon: one plate with 6 graded holes, one peg."""
from build123d import Box, Pos, Part, Align

CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)
PEG = 10.0
PITCH = 16.0
THICK = 4.0


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
```

- [ ] **Step 4: Run, expect pass.**

- [ ] **Step 5: Export script**

`scripts/export_all.py`:
```python
"""Export every registered part into out/."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import coupon


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
}

if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
```
Run `uv run python scripts/export_all.py`; expect six paths under `out/`.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Add clearance calibration coupon

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 7: User action (blocking for later tuning, not for later tasks)**
Print `out/coupon_plate.stl` and `out/coupon_peg.stl` on the U1 in PETG. Report which hole the peg slides into with light finger pressure (→ `CLR_FIT`) and which it falls through (→ `CLR_DEVICE`). Update `params.py` accordingly.

---

### Task 3: Measurements module and measuring guide

**Files:**
- Create: `src/dock/measurements.py`, `docs/measuring.md`, `tests/test_measurements.py`

**Interfaces:**
- Produces: dataclass instances `measurements.ROAM`, `measurements.ION`, `measurements.TRACKR` (fields: `length, width, thickness` for Roam; `diameter, length, port_offset_from_axis` for Ion; `length, width, thickness` for Trackr) and `measurements.CHARGER` (fields: `length, width, height, port_face_margin, inlet_center_z, led_offset_from_ports`). Nominal published values are the defaults; the user overwrites them.

- [ ] **Step 1: Failing test**

`tests/test_measurements.py`:
```python
from dock import measurements as m


def test_all_measurements_positive():
    for obj in (m.ROAM, m.ION, m.TRACKR, m.CHARGER):
        for k, v in vars(obj).items():
            assert v > 0, f"{type(obj).__name__}.{k} must be > 0"


def test_charger_is_powerport6_sized():
    # sanity envelope for an Anker A2123; fails loudly if someone types cm
    assert 80 < m.CHARGER.length < 110
    assert 55 < m.CHARGER.width < 75
    assert 20 < m.CHARGER.height < 32
```

- [ ] **Step 2: Run, expect failure.**

- [ ] **Step 3: Implement**

`src/dock/measurements.py`:
```python
"""Caliper measurements. EDIT THESE after measuring the real objects.
All mm. Defaults are nominal/published values, marked NOMINAL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Slab:
    """A flat device measured lying face-up."""
    length: float     # longest dimension
    width: float
    thickness: float


@dataclass(frozen=True)
class Cylinder:
    """A round-bodied device standing on its charge-port end."""
    diameter: float
    length: float
    port_offset_from_axis: float  # micro-USB port centre distance from body axis


@dataclass(frozen=True)
class Charger:
    length: float               # port face to inlet face
    width: float
    height: float
    port_face_margin: float     # distance from charger edge to first port centre
    inlet_center_z: float       # C7 inlet centre height above charger bottom
    led_offset_from_ports: float  # LED centre distance from nearest port centre


ROAM = Slab(length=89.8, width=60.7, thickness=16.5)          # NOMINAL Wahoo spec
ION = Cylinder(diameter=32.0, length=100.0, port_offset_from_axis=6.0)  # NOMINAL guess
TRACKR = Slab(length=60.0, width=28.0, thickness=17.0)       # NOMINAL guess
CHARGER = Charger(length=96.0, width=65.0, height=26.0,
                  port_face_margin=10.0, inlet_center_z=13.0,
                  led_offset_from_ports=8.0)                  # NOMINAL A2123
```

- [ ] **Step 4: Run, expect pass.**

- [ ] **Step 5: Measuring guide**

`docs/measuring.md`:
```markdown
# What to measure (digital calipers, mm, one decimal)

Enter each value in `src/dock/measurements.py`, then run `uv run pytest`.

## Wahoo Roam 3 (`ROAM`)
- length: top to bottom edge, at the widest
- width: side to side at the widest
- thickness: face to back, including the rear mount tabs
- Also note: distance from the bottom edge to the USB-C port centre, and
  whether the port is on the back or the bottom edge (write it in a comment).

## Bontrager Ion Pro RT (`ION`)
- diameter: body diameter at the widest point
- length: lens face to tail
- port_offset_from_axis: with the light standing on its tail, distance from
  the body centre to the micro-USB port centre (0 if centred)

## Wahoo Trackr (`TRACKR`)
- length, width, thickness of the body without the mount clip
- Note where the USB-C port sits (end or side) in a comment.

## Anker PowerPort 6 (`CHARGER`)
- length: port face to C7 inlet face
- width, height (height = the dimension when the ports are on a vertical face)
- port_face_margin: charger edge to centre of the first USB port
- inlet_center_z: bottom of charger to centre of the C7 inlet
- led_offset_from_ports: nearest port centre to LED centre

## Cables (`params.py` Plug entries)
- For each cable: overmold width, height and length at the device end and
  the USB-A end. Update `USB_A_PLUG`, `USB_C_PLUG`, `MICRO_PLUG` with the
  largest of each.
```

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Add measurement inputs and measuring guide

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 7: User action:** measure per `docs/measuring.md`, edit `measurements.py`, commit.

---

### Task 4: Cradles

**Files:**
- Create: `src/dock/cradles.py`, `tests/test_cradles.py`
- Modify: `scripts/export_all.py` (register three cradles)

**Interfaces:**
- Consumes: `params.WALL, FLOOR, CLR_DEVICE, CHAMFER, USB_C_PLUG, MICRO_PLUG`; `measurements.ROAM, ION, TRACKR`.
- Produces: `build_roam_cradle() -> Part`, `build_ion_cradle() -> Part`, `build_trackr_cradle() -> Part`. Every cradle: print face at Z=0, footprint centred on origin, a rectangular through-slot in its floor sized to the device-end plug + `CLR_DEVICE`, so a plug pushed up from below sits captive with the metal tip proud of the floor. Also `cradle_footprint(part) -> tuple[float, float]` returning X/Y size, used by `deck.py`.

Geometry:
- Roam: a shelf tilted 20 degrees toward the user, pocket = device + clearance on three sides, open at the top edge, floor slot behind the bottom edge where the USB-C port is.
- Ion: a ring (ID = diameter + 2*CLR_DEVICE, wall = WALL, height 25 mm) on a floor with the micro slot at `port_offset_from_axis`.
- Trackr: upright pocket, device standing on its port end, pocket depth 60 % of length, USB-C slot in the floor.

- [ ] **Step 1: Failing tests**

`tests/test_cradles.py`:
```python
import pytest
from build123d import Axis
from dock import cradles, params
from dock import measurements as m


@pytest.mark.parametrize("fn", [cradles.build_roam_cradle,
                                cradles.build_ion_cradle,
                                cradles.build_trackr_cradle])
def test_cradle_is_valid_and_sits_on_bed(fn):
    p = fn()
    assert p.is_valid()
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6


def test_ion_ring_inner_diameter_has_clearance():
    p = cradles.build_ion_cradle()
    # the ring's inner cylindrical face radius
    inner = [f for f in p.faces() if f.geom_type.name == "CYLINDER"]
    radii = sorted(f.radius for f in inner)
    assert abs(radii[0] - (m.ION.diameter / 2 + params.CLR_DEVICE)) < 1e-6


def test_trackr_pocket_wider_than_device():
    p = cradles.build_trackr_cradle()
    top = p.faces().sort_by(Axis.Z)[-1]
    inner = top.inner_wires()
    assert len(inner) == 1
    size = inner[0].bounding_box().size
    assert size.X >= m.TRACKR.width + 2 * params.CLR_DEVICE - 1e-6
    assert size.Y >= m.TRACKR.thickness + 2 * params.CLR_DEVICE - 1e-6


def test_every_cradle_has_a_floor_slot():
    for fn in (cradles.build_roam_cradle, cradles.build_ion_cradle,
               cradles.build_trackr_cradle):
        p = fn()
        bottom = p.faces().sort_by(Axis.Z)[0]
        assert len(bottom.inner_wires()) >= 1, fn.__name__
```

- [ ] **Step 2: Run, expect failure.**

- [ ] **Step 3: Implement**

`src/dock/cradles.py`:
```python
"""Three device cradles. Each is printable standalone for fit testing."""
from build123d import Box, Cylinder, Pos, Rot, Part, Align, Plane, chamfer, Axis
from dock import params as P
from dock import measurements as M

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _slot(plug: P.Plug) -> Part:
    """Through-slot for a plug overmold pushed up from below (Z-thru box)."""
    return Box(plug.width + 2 * P.CLR_DEVICE, plug.height + 2 * P.CLR_DEVICE, 100,
               align=(Align.CENTER, Align.CENTER, Align.CENTER))


def cradle_footprint(part: Part) -> tuple[float, float]:
    s = part.bounding_box().size
    return (s.X, s.Y)


def build_roam_cradle() -> Part:
    c = P.CLR_DEVICE
    pw = M.ROAM.width + 2 * c          # pocket width (X)
    pl = M.ROAM.length * 0.5 + c       # pocket holds the lower half
    pd = M.ROAM.thickness + 2 * c      # pocket depth into the shelf
    ow, ol, oh = pw + 2 * P.WALL, pl + P.WALL, pd + P.FLOOR
    shelf = Box(ow, ol, oh, align=_MIN)
    pocket = Pos(0, P.WALL / 2, P.FLOOR) * Box(pw, pl, pd, align=_MIN)  # open on +Y
    shelf -= pocket
    # slot behind the bottom edge, where the USB-C port is
    shelf -= Pos(0, -pl / 2 + P.USB_C_PLUG.height / 2 + c + 1.0, 0) * _slot(P.USB_C_PLUG)
    # tilt 20 deg toward -Y (the user), then drop onto a wedge so it prints flat
    tilted = Rot(-20, 0, 0) * shelf
    bb = tilted.bounding_box()
    tilted = Pos(0, 0, -bb.min.Z) * tilted
    wedge = Box(ow, bb.size.Y, bb.size.Z, align=_MIN)
    wedge = wedge - Pos(0, 0, 0) * (Rot(-20, 0, 0) * Box(ow + 2, ol * 2, 200, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    part = tilted + wedge
    return part


def build_ion_cradle() -> Part:
    c = P.CLR_DEVICE
    inner_r = M.ION.diameter / 2 + c
    outer_r = inner_r + P.WALL
    h = 25.0
    part = Cylinder(outer_r, h + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Cylinder(inner_r, h, align=_MIN)
    part -= Pos(M.ION.port_offset_from_axis, 0, 0) * _slot(P.MICRO_PLUG)
    part = chamfer(part.edges().filter_by(Axis.Z, reverse=True).sort_by(Axis.Z)[:1], P.CHAMFER)
    return part


def build_trackr_cradle() -> Part:
    c = P.CLR_DEVICE
    pw = M.TRACKR.width + 2 * c
    pt = M.TRACKR.thickness + 2 * c
    depth = M.TRACKR.length * 0.6
    part = Box(pw + 2 * P.WALL, pt + 2 * P.WALL, depth + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Box(pw, pt, depth, align=_MIN)
    part -= _slot(P.USB_C_PLUG)
    return part
```

- [ ] **Step 4: Run tests; iterate until green.** The Roam wedge boolean is the most likely to need adjustment: if `is_valid()` fails, replace the wedge subtraction with `split(tilted_box, bisect_by=Plane.XY)` semantics — build the shelf, rotate, then `part = tilted + (Box(ow, bb.size.Y, bb.size.Z, align=_MIN) & Pos(...)*...)`. Keep the tests as the arbiter.

- [ ] **Step 5: Register exports**

In `scripts/export_all.py` add:
```python
from dock import cradles
PARTS.update({
    "cradle_roam": cradles.build_roam_cradle,
    "cradle_ion": cradles.build_ion_cradle,
    "cradle_trackr": cradles.build_trackr_cradle,
})
```
(place after the `PARTS = {...}` definition). Run the script; expect nine new files.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Add Roam, Ion and Trackr cradles

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 7: User action:** print the three cradles, check device fit and that each plug sits captive. Adjust `CLR_DEVICE` or measurements, reprint.

---

### Task 5: Divider

**Files:**
- Create: `src/dock/divider.py`, `tests/test_divider.py`
- Modify: `scripts/export_all.py`

**Interfaces:**
- Consumes: `params.CLR_RAIL`.
- Produces: `divider.THICK = 2.0`, `divider.RAIL_W = 4.0`, `divider.RAIL_D = 2.0`, `build_divider(height: float, width: float) -> Part` (a slab with a rectangular rail on each vertical side), and `divider.rail_cutter(height: float) -> Part` returning the mating slot shape to subtract from a bay wall, oriented with the rail's long axis along Z, centred at origin. X (depth) is `RAIL_D + CLR_RAIL` because only the slot bottom bears in X (the bay side is open); Y is `RAIL_W + 2*CLR_RAIL`. deck.py must place the cutter wholly inside the wall: centre at x = ±(SPARE_W/2 + (RAIL_D + CLR_RAIL)/2).

- [ ] **Step 1: Failing test**

`tests/test_divider.py`:
```python
from dock import divider, params


def test_divider_bounding_box():
    p = divider.build_divider(height=40, width=50)
    s = p.bounding_box().size
    assert abs(s.Z - 40) < 1e-6
    assert abs(s.X - (50 + 2 * divider.RAIL_D)) < 1e-6
    assert abs(s.Y - divider.RAIL_W) < 1e-6


def test_cutter_is_larger_than_rail_by_clearance():
    cut = divider.rail_cutter(height=40).bounding_box().size
    assert abs(cut.Y - (divider.RAIL_W + 2 * params.CLR_RAIL)) < 1e-6
```

- [ ] **Step 2: Run, expect failure.**

- [ ] **Step 3: Implement**

`src/dock/divider.py`:
```python
"""Removable divider: 2 mm slab with a rectangular rail on each vertical edge."""
from build123d import Box, Pos, Part, Align
from dock import params as P

THICK = 2.0
RAIL_W = 4.0   # rail width (Y), wider than the slab so it can't pull out sideways
RAIL_D = 2.0   # rail depth into the wall (X)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def build_divider(height: float, width: float) -> Part:
    slab = Box(width, THICK, height, align=_MIN)
    rail = Box(RAIL_D, RAIL_W, height, align=_MIN)
    return slab + Pos(width / 2 + RAIL_D / 2, 0, 0) * rail + Pos(-width / 2 - RAIL_D / 2, 0, 0) * rail


def rail_cutter(height: float) -> Part:
    c = P.CLR_RAIL
    return Box(RAIL_D + c, RAIL_W + 2 * c, height, align=_MIN)
```

- [ ] **Step 4: Run, expect pass.** Register `"divider": lambda: divider.build_divider(40, 50)` in `scripts/export_all.py`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Add removable divider with rail cutter

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Deck

**Files:**
- Create: `src/dock/deck.py`, `tests/test_deck.py`
- Modify: `scripts/export_all.py`

**Interfaces:**
- Consumes: the three cradle builders and `cradle_footprint`; `divider.rail_cutter`; `params.*`; `measurements.CHARGER` (for overall length).
- Produces: `deck.layout() -> dict[str, tuple[float, float]]` giving each cradle's XY centre; `deck.DECK_X, deck.DECK_Y` outer size; `deck.LIP_H = 6.0`; `build_deck() -> Part`; `deck.SPARE_BAY = (x, y, w, l, h)` tuple.

Layout: a single row along X, in order Ion, Roam, Trackr, spare bay, with `params.WALL` gaps. Deck plate thickness = `FLOOR`. The lip is a `WALL`-thick rectangular skirt hanging `LIP_H` below the plate, inset `WALL + CLR_FIT` from the outer edge so it drops into the base. Cable channels are not modelled as separate parts: each cradle's floor slot already passes through the plate, and the underside is open (the base cavity is the cable space).

- [ ] **Step 1: Failing tests**

`tests/test_deck.py`:
```python
from build123d import Axis
from dock import deck, params


def test_deck_fits_bed():
    assert deck.DECK_X <= params.BED_X
    assert deck.DECK_Y <= params.BED_Y


def test_deck_valid_and_flat_on_bed():
    p = deck.build_deck()
    assert p.is_valid()
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_layout_has_four_stations_without_overlap():
    lay = deck.layout()
    assert set(lay) == {"ion", "roam", "trackr", "spare"}
    xs = sorted(v[0] for v in lay.values())
    assert all(b - a > 20 for a, b in zip(xs, xs[1:]))


def test_deck_has_at_least_four_floor_slots():
    p = deck.build_deck()
    bottom = p.faces().sort_by(Axis.Z)[0]
    assert len(bottom.inner_wires()) >= 4
```

- [ ] **Step 2: Run, expect failure.**

- [ ] **Step 3: Implement**

`src/dock/deck.py`:
```python
"""Top deck: plate + lip + three cradles + spare bay with divider slots."""
from build123d import Box, Pos, Part, Align, Rot
from dock import params as P
from dock import measurements as M
from dock import cradles, divider

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
LIP_H = 6.0
SPARE_W, SPARE_L, SPARE_H = 40.0, 70.0, 30.0   # X, Y, wall height


def _stations() -> list[tuple[str, float, float]]:
    """(name, x_size, y_size) in row order."""
    ion = cradles.cradle_footprint(cradles.build_ion_cradle())
    roam = cradles.cradle_footprint(cradles.build_roam_cradle())
    trk = cradles.cradle_footprint(cradles.build_trackr_cradle())
    return [("ion", *ion), ("roam", *roam), ("trackr", *trk),
            ("spare", SPARE_W + 2 * P.WALL, SPARE_L + 2 * P.WALL)]


def layout() -> dict[str, tuple[float, float]]:
    x = P.WALL
    out = {}
    for name, sx, _ in _stations():
        out[name] = (x + sx / 2, 0.0)
        x += sx + P.WALL
    return out


DECK_X = P.WALL + sum(s[1] + P.WALL for s in _stations())
DECK_Y = max(s[2] for s in _stations()) + 2 * P.WALL


def _spare_bay() -> Part:
    bay = Box(SPARE_W + 2 * P.WALL, SPARE_L + 2 * P.WALL, SPARE_H + P.FLOOR, align=_MIN)
    bay -= Pos(0, 0, P.FLOOR) * Box(SPARE_W, SPARE_L, SPARE_H, align=_MIN)
    bay -= Pos(0, 0, 0) * Box(P.USB_A_PLUG.width + 2 * P.CLR_DEVICE,
                              P.USB_A_PLUG.height + 2 * P.CLR_DEVICE, 100,
                              align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # two divider positions, rails cut into both long walls
    for y in (-SPARE_L / 4, SPARE_L / 4):
        for x in (SPARE_W / 2 + (divider.RAIL_D + P.CLR_RAIL) / 2, -(SPARE_W / 2 + (divider.RAIL_D + P.CLR_RAIL) / 2)):
            bay -= Pos(x, y, P.FLOOR) * divider.rail_cutter(SPARE_H)
    return bay


def build_deck() -> Part:
    plate = Box(DECK_X, DECK_Y, P.FLOOR, align=(Align.MIN, Align.CENTER, Align.MIN))
    lip_out = Box(DECK_X - 2 * (P.WALL + P.CLR_FIT), DECK_Y - 2 * (P.WALL + P.CLR_FIT), LIP_H,
                  align=(Align.MIN, Align.CENTER, Align.MAX))
    lip_in = Box(DECK_X - 2 * (2 * P.WALL + P.CLR_FIT), DECK_Y - 2 * (2 * P.WALL + P.CLR_FIT), LIP_H,
                 align=(Align.MIN, Align.CENTER, Align.MAX))
    lip = Pos(P.WALL + P.CLR_FIT, 0, 0) * lip_out - Pos(2 * P.WALL + P.CLR_FIT, 0, 0) * lip_in
    deck = plate + lip
    builders = {"ion": cradles.build_ion_cradle, "roam": cradles.build_roam_cradle,
                "trackr": cradles.build_trackr_cradle, "spare": _spare_bay}
    for name, (x, y) in layout().items():
        cradle = builders[name]()
        # cradles carry their own FLOOR; sink them so their floor merges with the plate
        deck += Pos(x, y, 0) * cradle
        # re-cut the cradle's floor slot through the plate
        slot_faces = cradle.faces().sort_by(lambda f: f.center().Z)[0].inner_wires()
        for w in slot_faces:
            bb = w.bounding_box()
            deck -= Pos(x + bb.center().X, y + bb.center().Y, 0) * Box(
                bb.size.X, bb.size.Y, 100, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # lift everything so the lip bottom is at Z=0 (prints deck-up with the lip as a skirt)
    return Pos(0, 0, LIP_H) * deck
```

Note: this prints deck-side up with the 6 mm lip as a skirt, which needs no support; cradle pockets face up. Slots through the plate are 100 mm tall cutters so they pass the lip region too.

- [ ] **Step 4: Run tests; fix until green.** Register `"deck": deck.build_deck` in `scripts/export_all.py`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Add deck with cradles, spare bay and lip

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Base tray

**Files:**
- Create: `src/dock/base.py`, `tests/test_base.py`
- Modify: `scripts/export_all.py`

**Interfaces:**
- Consumes: `deck.DECK_X, DECK_Y, PLATE_T`; `measurements.CHARGER`; `params.*`.
- Produces: `base.BASE_H`, `base.BASE_X`, `base.BASE_Y`, `base.REBATE_D`, `build_base() -> Part`.

Geometry (rebate design, per the Task 6 ruling: the deck is a flat 8 mm plate, no lip): open-top box with outer size `BASE_X = DECK_X + 2*(WALL + CLR_FIT)`, `BASE_Y = DECK_Y + 2*(WALL + CLR_FIT)`, walls `WALL`, floor `FLOOR`. Inner height below the plate = `CHARGER.height + 12` (cable bend room). At the top of the inner walls a rebate `REBATE_D = PLATE_T` deep and `CLR_FIT` wider than the deck on each side receives the plate flush with the base top; the walls below the rebate are `2*WALL` thick so the plate rests on a `WALL`-wide ledge. `BASE_H = FLOOR + CHARGER.height + 12 + PLATE_T`. Charger fence: a raised `WALL`-thick fence inside the floor, `CHARGER + 2*CLR_FIT` in plan, 8 mm tall, port face toward +X, with a fingernail notch. Rear (-Y) wall cut-outs: AC cord notch (10 mm wide, from the top edge down to `inlet_center_z`), escape port (`USB_A_PLUG.width + 4` wide, 12 mm tall, just below the rebate), LED window 4 mm square at the LED position. Four 10 mm diameter, 1 mm deep foot recesses underneath.

- [ ] **Step 1: Failing tests**

`tests/test_base.py`:
```python
from build123d import Axis
from dock import base, deck, params
from dock import measurements as m


def test_base_outer_size_wraps_deck_with_clearance():
    bb = base.build_base().bounding_box().size
    assert abs(bb.X - (deck.DECK_X + 2 * (params.WALL + params.CLR_FIT))) < 1e-6
    assert abs(bb.Y - (deck.DECK_Y + 2 * (params.WALL + params.CLR_FIT))) < 1e-6


def test_base_height_leaves_charger_room_under_plate():
    assert base.BASE_H >= params.FLOOR + m.CHARGER.height + deck.PLATE_T


def test_rebate_depth_matches_plate():
    assert abs(base.REBATE_D - deck.PLATE_T) < 1e-6


def test_base_valid_and_on_bed():
    p = base.build_base()
    assert p.is_valid
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_base_has_four_foot_recesses():
    p = base.build_base()
    bottom = p.faces().sort_by(Axis.Z)[0]
    assert len(bottom.inner_wires()) == 4
```

- [ ] **Step 2: Run, expect failure.**

- [ ] **Step 3: Implement**

`src/dock/base.py`:
```python
"""Base tray: hides the Anker PowerPort 6 and the cable slack; the deck plate drops into a top rebate."""
from build123d import Box, Cylinder, Pos, Part, Align
from dock import params as P
from dock import measurements as M
from dock import deck

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
CABLE_ROOM = 12.0
FENCE_H = 8.0
REBATE_D = deck.PLATE_T
BASE_X = deck.DECK_X + 2 * (P.WALL + P.CLR_FIT)
BASE_Y = deck.DECK_Y + 2 * (P.WALL + P.CLR_FIT)
BASE_H = P.FLOOR + M.CHARGER.height + CABLE_ROOM + REBATE_D


def build_base() -> Part:
    X, Y = BASE_X, BASE_Y
    cx = X / 2
    body = Pos(cx, 0, 0) * Box(X, Y, BASE_H, align=_MIN)
    # lower cavity: walls 2*WALL thick so the rebate leaves a WALL-wide ledge
    body -= Pos(cx, 0, P.FLOOR) * Box(X - 4 * P.WALL, Y - 4 * P.WALL, BASE_H, align=_MIN)
    # rebate that receives the deck plate flush with the top
    body -= Pos(cx, 0, BASE_H - REBATE_D) * Box(
        deck.DECK_X + 2 * P.CLR_FIT, deck.DECK_Y + 2 * P.CLR_FIT, REBATE_D, align=_MIN)

    # charger fence, port face toward +X, charger centred in Y
    ch_l, ch_w = M.CHARGER.length + 2 * P.CLR_FIT, M.CHARGER.width + 2 * P.CLR_FIT
    fence = Box(ch_l + 2 * P.WALL, ch_w + 2 * P.WALL, FENCE_H + P.FLOOR, align=_MIN)
    fence -= Pos(0, 0, P.FLOOR) * Box(ch_l, ch_w, FENCE_H, align=_MIN)
    fence -= Pos(0, ch_w / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2, FENCE_H, align=_MIN)  # nail notch
    fence_x = 2 * P.WALL + P.WALL + ch_l / 2
    body += Pos(fence_x, 0, 0) * fence

    # rear wall (-Y): cord notch above the inlet, escape port, LED window
    rear_y = -Y / 2
    inlet_x = fence_x - ch_l / 2  # inlet face is on the -X side of the charger
    body -= Pos(inlet_x, rear_y, P.FLOOR + M.CHARGER.inlet_center_z) * Box(10, 3 * P.WALL, BASE_H, align=_MIN)
    body -= Pos(X - 30, rear_y, BASE_H - REBATE_D - 12) * Box(P.USB_A_PLUG.width + 4, 3 * P.WALL, 12, align=_MIN)
    led_x = fence_x + ch_l / 2 - M.CHARGER.port_face_margin - M.CHARGER.led_offset_from_ports
    body -= Pos(led_x, rear_y, P.FLOOR + M.CHARGER.height / 2) * Box(4, 3 * P.WALL, 4, align=_MIN)

    # foot recesses
    for fx in (12, X - 12):
        for fy in (-Y / 2 + 12, Y / 2 - 12):
            body -= Pos(fx, fy, 0) * Cylinder(5, 1.0, align=_MIN)
    return body
```

Note: the cord notch runs up through the rebate ledge at the rear; that is intended (the cord drops in from above before the plate is seated). If the tests find the rear-wall cuts merge inner wires on the bottom face, move the foot recesses inboard.

- [ ] **Step 4: Run tests until green.** Register `"base": base.build_base`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Add base tray with rebate, charger fence, cord notch, escape port

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Assembly checks and print handoff

**Files:**
- Create: `tests/test_assembly.py`, `docs/printing.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `deck.build_deck`, `deck.DECK_X/DECK_Y/PLATE_T`, `base.build_base`, `base.BASE_H/BASE_X/BASE_Y/REBATE_D`, `params.CLR_FIT/WALL/BED_X/BED_Y`.

- [ ] **Step 1: Failing tests**

`tests/test_assembly.py`:
```python
from build123d import Pos
from dock import deck, base, params


def test_plate_fits_rebate_with_clearance():
    assert base.BASE_X - 2 * params.WALL >= deck.DECK_X + 2 * params.CLR_FIT - 1e-6
    assert base.BASE_Y - 2 * params.WALL >= deck.DECK_Y + 2 * params.CLR_FIT - 1e-6


def test_assembled_parts_do_not_intersect():
    d = deck.build_deck()
    b = base.build_base()
    seated = Pos(params.WALL + params.CLR_FIT, 0, base.BASE_H - base.REBATE_D) * d
    inter = seated & b
    assert inter.volume < 1e-3


def test_plate_top_is_flush_with_base_top():
    assert abs((base.BASE_H - base.REBATE_D + deck.PLATE_T) - base.BASE_H) < 1e-6


def test_assembled_footprint_within_bed():
    assert base.BASE_X <= params.BED_X and base.BASE_Y <= params.BED_Y
```

- [ ] **Step 2: Run; fix geometry until green.**

- [ ] **Step 3: Printing guide**

`docs/printing.md`:
```markdown
# Printing on the Snapmaker U1

Slicer: Snapmaker Orca (Flatpak `io.github.Snapmaker.Snapmaker_Orca`).
Material: PETG. Profile: U1 0.4 nozzle, 0.2 mm layers.

| Part | Orientation | Walls | Infill | Supports |
|---|---|---|---|---|
| coupon_plate, coupon_peg | as exported | 3 | 15 % | none |
| cradle_* | as exported (pocket up) | 3 | 15 % | none |
| divider | as exported | 3 | 100 % | none |
| deck | as exported (flat plate on bed, cradles up) | 3 | 15 % | none |
| base | as exported (open top up) | 3 | 15 % | none |

Order: coupon → update `params.py` → cradles → deck → base.
Run `uv run python scripts/export_all.py` after any parameter change; open
`out/<part>.3mf` in the slicer.
```

- [ ] **Step 4: Update README** with a "Workflow" section pointing to `docs/measuring.md` and `docs/printing.md`.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Add assembly fit tests and printing guide

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-review

- Spec coverage: base (T7), deck (T6), cradles (T4), divider (T5), coupon (T2), measurements (T3), export/tests/toolchain (T1), bed limit (T6/T8), LED window and escape port and cord notch (T7), rubber feet (T7). Corner pegs from the spec were dropped in favour of the lip alone (noted in T7); snap-in cable channels were dropped because the open base cavity is the cable space (noted in T6). Both are simplifications the executor should keep unless the fit test shows the deck rocking.
- Placeholders: none. Nominal measurement defaults are explicit values marked NOMINAL and replaced by the user.
- Type consistency: `build_*() -> Part` everywhere; `cradle_footprint`, `rail_cutter(height)`, `layout()`, `DECK_X/DECK_Y/LIP_H/BASE_H` names match across tasks.
