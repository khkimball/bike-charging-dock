# Charging Dock — Tapered Dock Design Spec (physical v2)

Date: 2026-09-23
Status: approved in chat, sections 1–3
Supersedes: the exterior, lid, divider and base-wall parts of
2026-09-20-tray-dock-design.md. The bay layout, devices, charger and cable
routing carry over unless changed here.
Reference: the printed and accepted v1 prototype is tagged `v1-prototype`
(STLs in releases/v1-prototype/).

## Goals

1. **Print efficiency**: at least 25 % less print time *and* filament than
   the v1 set, measured the same way (see Verification).
2. **Match the Trek CHRGtime exterior**: one continuous trapezoid from the
   lid top to the foot. The reference's walls lean about 15° off vertical,
   measured from the manual's to-scale front view (p. 3) and close-up (p. 7).

v1 fit was fine in use, and the Anker A2154 fits the v1 fence as modelled, so
clearances, bay sizes and the charger numbers carry over (the charger values
stay marked NOMINAL until measured).

## Exterior

- **Taper**: a single 15° draft (TAPER_DEG) on every outer face of the base
  and lid. It is a true draft: at depth d below the rim the outline is the rim
  outline offset inward by d·tan 15°, and the corner radius shrinks by the
  same amount.
- **Corners**: R30 at the base rim (CORNER_R), shrinking to about R8 at the
  foot. The lid's corners continue the same surface upward (radius grows
  with height).
- **Size (derived, not frozen)**: rim ≈ 242 × 174, foot ≈ 198 × 130, base
  height 81.6 as in v1 (FLOOR + charger + CABLE_ROOM + tray height).
  Everything grows from the tray; nothing is hard-coded.
- **Two-tone base**: dark foot band, light body. The colour line is at
  BAND_H = 8 mm, below the cord port's sill (Z 10.1), so both kinds of port
  sit entirely in the light body. A reveal groove 1.2 mm tall × 0.6 mm deep,
  V-profiled at 45°, is centred on the colour line. The tool change can be
  set at any layer inside the groove, so it works at both 0.20 and 0.28 mm
  layers. One tool change per base; no painted colour.
- **Lid**: LID_H = 8 mm tall with a 2.0 mm top plate (LID_PLATE) and 1.6 mm
  walls (THIN_WALL). The lower 5 mm continues the 15° slope from the base
  rim; the top 3 mm is a flared lip standing 2 mm proud of the slope. The lip
  is the finger grip for opening and echoes the reference's flared lid edge.
  It sits flush on the base rim with no skirt; the hinge locates it. It
  prints top-face-down: its walls lean inward as they rise, so there is no
  overhang. The bed-face edge gets the usual 1 mm chamfer.
- **Removed**: the v1 plinth (the full taper replaces it), the lid skirt,
  the rim rebate and the rim finger notches.
- **Bed limit**: the lid is the largest part (≈ 250 × 182 with the lip). If
  a derived size exceeds BED_X/BED_Y (250) the lip width shrinks first;
  the U1's physical bed is 270.

## Tray

One print, plate down, bays up, no supports.

- **Shell**: its outer walls lean at 15°, parallel to the base wall, and are
  THIN_WALL (1.6) thick; they are hidden inside the base. Plate TRAY_PLATE
  = 2.0 (was 3.0). Its rim is flush with the base rim.
- **Bays**: the same four bays and devices as v1 (ROAM on the left, long
  axis along Y; Ion Pro RT, TRACKR and spare stacked in the right column).
  Bay floors are sized to device + CLR_BAY_OUTER (3.0) at the sloped outer
  walls, which opens to about 13 mm at the top for cables, and device +
  CLR_BAY (8.0) at the vertical internal walls, as in v1. BAY_DEPTH stays 38.
- **Cable cutouts**: unchanged, 28 × 16, one at each bay's outer end; the
  Ion bay keeps three along its length (UNDERSIDE_PORT_CUTOUTS). They sit
  within each bay's floor, clear of the sloped wall.
- **Fixed internal walls**: the centre partition and the two right-column
  dividers are fused to the plate and outer walls, full bay depth, WALL (2.4)
  thick. There are no rail slots and no RAIL_WALL thickening.
- **Rounding**:
  - R6 on every vertical inside corner, where internal walls meet each other
    or an outer wall.
  - R3 where every wall meets the bay floor.
  - A full round on the top edge of every internal wall.

  All of these face up or sideways, so the chamfer-on-downward-edges rule
  does not apply.
- **Lift-out**: a finger slot through the centre partition near its top,
  about 25 wide × 15 tall with a pointed-arch (45°) head so it prints
  unsupported. It replaces the rim notches.

## Base

Prints open-top-up. Supports are for the cord port only.

- **Shell**: a single WALL (2.4) sloped wall and a FLOOR (1.6) floor. This
  replaces v1's 2·WALL lower walls, which existed only to carry the rebate
  ledge.
- **Tray ledge**: a continuous ring on the inner wall at the tray's floor
  depth that the tray rests on. It stands 2.5 mm proud of the wall and is
  chamfered 45° underneath, so it prints unsupported. The tray's outer wall
  runs CLR_FIT + 0.3 clear of the base wall, so the ledge sets the tray's
  height, not a taper wedge.
- **Charger**: the v1 U fence, backed onto the −X end wall. That wall leans
  away above the floor, so POCKET_BACK_SLACK (2) is measured at floor level.
  CABLE_ROOM stays 6. Two changes from v1:
  - **Rounded to the charger**: the A2154's vertical edges are rounded. A new
    measurement field, `Charger.corner_r` (NOMINAL until measured; see
    docs/measuring.md), sets the fillet on the pocket's two inner vertical
    corners at the port-face end: corner_r + CLR_FIT, concentric with the
    charger's own edge. The fence's outer vertical corners are rounded
    corner_r + CLR_FIT + WALL, so the U keeps a uniform WALL through each
    bend.
  - **No fingernail notch**: v1's notch in the +Y fence wall is removed.
    The charger lifts out easily without it.
- **Cord port**: unchanged, a 26 × 16 rectangle through the −X wall,
  centred on the inlet. It is still the one supported ceiling
  (SUPPORTED_CEILINGS).
- **Escape ports**: two stadium-shaped holes (nearly oval, about 14 × 8
  with full R4 ends) in the −X wall, one each side of the fence. Each is
  centred in Y in the gap between the fence and the side wall, with its sill
  above the colour line. This replaces the single port above the cord port,
  which the charger's height covered. Each port's width is derived so that a
  full WALL of material remains to the corner arc at that height. Their 6 mm
  flat heads are short bridges.
- **Tie grid and feet**: the tie-down grid (Ø4 on a 24 mm pitch) and the
  four foot recesses stay, re-fitted to the smaller tapered floor.
- **Rim**: plain WALL rim, with no rebate and no notches.
- **Hinge knuckles**: see below.

## Hinge

Snap-on and lift-off, with no hardware. It sits on the +Y long side, at two
stations about 60 mm in from each end.

- **Base**: each station has two cheeks with a horizontal Ø5 pin between
  them. The pin axis runs along X, just outside the rim at rim height. The
  pin has a teardrop profile with its 45° point down, and the cheeks'
  undersides are chamfered 45° into the sloped wall, so everything prints
  without supports.
- **Lid**: a C-hook at each station wraps about 270° of the pin. Its mouth
  is narrower than the pin by a snap interference (initially 0.4 mm, with
  0.3 mm pin-to-bore clearance; both tuned from the hinge coupon) and faces so that the hook passes over the pin only at the fully
  open angle (≈ 110°). At 110° a heel on the lid rests against the base
  cheeks, so the lid stays open on its own. Below that angle the lid is
  captive.
- **Hinge coupon**: `coupon.py` gains a small hinge coupon (one base pin
  station plus one lid hook) that tunes the pin clearance and snap
  interference before the base is printed.

## Removed parts and code

- The `divider` part and `divider.py`, with its tests and its export entry.
- Rail slots, RAIL_WALL and CLR_RAIL. CLR_RAIL stays only if the coupon
  still uses it.
- The plinth, rebate, rim notch, fence fingernail notch and
  single-escape-port geometry, with their tests.

## Print efficiency and verification

- **Baseline** (v1, PETG, U1 0.20 Standard, 3 walls, 15 % infill, base with
  supports):

  | Part | Time | Grams |
  |---|---|---|
  | Base | 5 h 55 m | 266 |
  | Tray | 4 h 22 m | 186 |
  | Lid | 2 h 15 m | 105 |
  | Divider × 2 | 1 h 28 m | 31 |
  | **Total** | **14 h 00 m** | **588** |

- **Target**: the v2 set at 0.20 is at least 25 % below the baseline in both
  time and grams. The 0.28 mm draft layer for the base and lid is reported
  alongside and recommended in docs/printing.md if it slices cleanly.
- **scripts/slice_report.py**: a new, committed script that slices every
  exported part headlessly with the Snapmaker Orca Flatpak and prints a
  part | time | grams table next to the v1 baseline. Known quirks it must
  handle:
  - It flattens the vendor U1, process and Generic PETG profiles' `inherits`
    chains at run time and keeps `"from": "system"`.
  - It drops the `wipe_tower_filament` key, which segfaults the CLI.
  - It passes `--export-3mf` a bare filename.
  - It reads the estimates from the gcode header inside the exported 3mf.
  - It is not part of pytest.
- **Two-tone cost**: the prime/wipe tower is off for the single tool change;
  docs/printing.md says so, and the report measures the band's real cost.
- **Tests** (pytest, all measuring the built solids):
  - **Taper**: the outline sampled at several heights leans 15° ± 0.5°; the
    corner radius is ≈ R30 at the rim and ≈ R8 at the foot.
  - **Walls**: wall thickness ≥ WALL everywhere, including around both
    escape ports and the cord port.
  - **Tray fit**: seated on the ledge, the tray does not intersect the base,
    its rim is flush within 0.5 mm, and every bay floor holds its device
    plus the specified clearance.
  - **Lid**: it lies flush on the rim, and swept from 0° to 110° about the
    hinge axis it intersects neither the base nor the seated tray, except
    at the heel stop at 110°.
  - **Printability**: no downward face past 45°. The only allowlisted
    bridges are the escape port heads and the foot recesses; the finger slot
    and the hinge pin and bore are 45° teardrops or arches, so they need no
    bridge. The cord port is the only supported ceiling.
  - **Parts**: every exported part is a single valid solid with its bed face
    at Z = 0 and fits BED_X × BED_Y.
  - **Colour line**: the groove is at BAND_H, and both kinds of port are
    wholly above it.

## Docs

- docs/printing.md:
  - part table: the divider row goes and the hinge coupon row is added
  - two-tone base: the tool-change layer, and the prime tower off
  - the 0.28 draft profile
  - hinge assembly: snap the lid on at full open
- docs/measuring.md: how to measure the charger's corner radius
  (`Charger.corner_r`).
- CLAUDE.md: note scripts/slice_report.py and the efficiency target.

## Out of scope

Lid latch or magnets, lettering, stickers, LED window, remeasuring the
devices (still NOMINAL, and v1 fit was fine). The charger's corner radius is
the one new measurement.
