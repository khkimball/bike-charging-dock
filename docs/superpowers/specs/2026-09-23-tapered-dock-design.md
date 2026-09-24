# Charging Dock — Tapered Dock Design Spec (physical v2)

Date: 2026-09-23
Status: implemented on branch tapered-dock (plan docs/superpowers/plans/2026-09-24-tapered-dock.md)
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
- **Size (derived, not frozen)**: rim ≈ 243 × 178, foot ≈ 200 × 135, base
  height ≈ 79.7 (FLOOR + charger + CABLE_ROOM + TRAY_SINK + tray height).
  Everything grows from the tray; nothing is hard-coded.
- **Two-tone base**: dark foot band, light body. The colour line is at
  BAND_H = 8 mm; both kinds of wall port have their sill clamped to sit at
  least 0.5 mm above the groove's top flank (`BAND_H + GROOVE_UP + 0.5`,
  taking whatever is higher against the port's own geometry), so both sit
  entirely in the light body. A reveal groove 1.2 mm tall × 0.6 mm deep is
  centred on the colour line, with asymmetric flanks -- 0.3 mm below, 0.9 mm
  above -- rather than a symmetric 45° V, which would overhang about 52°
  once drafted by TAPER_DEG. The tool change can be set at any layer inside
  the groove, so it works at both 0.20 and 0.28 mm layers. One tool change
  per base; no painted colour.
- **Lid**: LID_H = 8 mm tall with a 1.2 mm top plate (LID_PLATE) and 1.6 mm
  walls (THIN_WALL). The lower 5 mm continues the 15° slope from the base
  rim; the top 3 mm is a flared lip standing 2 mm proud of the slope. The lip
  is the finger grip for opening and echoes the reference's flared lid edge.
  It sits flush on the base rim with no skirt; the hinge locates it. It
  prints top-face-down: its walls lean inward as they rise, so there is no
  overhang. The bed-face edge gets the usual 1 mm chamfer.
- **Removed**: the v1 plinth (the full taper replaces it), the lid skirt,
  the rim rebate and the rim finger notches.
- **Bed limit**: the lid is the largest part (≈ 249.5 × 192 with the lip and hinge hooks). If
  a derived size exceeds BED_X/BED_Y (250) the lip width shrinks first;
  the U1's physical bed is 270.

## Tray

One print, plate down, bays up, no supports.

- **Shell**: its outer walls lean at 15°, parallel to the base wall, and are
  THIN_WALL (1.6) thick; they are hidden inside the base. Plate TRAY_PLATE
  = 1.2 (was 3.0). Its rim is flush with the base rim.
- **Bays**: the same four bays and devices as v1 (ROAM on the left, long
  axis along Y; Ion Pro RT, TRACKR and spare stacked in the right column).
  Bay floors are sized to device + CLR_BAY_OUTER (3.0) at the sloped outer
  walls, which opens to about 13 mm at the top for cables, and device +
  CLR_BAY (8.0) at the vertical internal walls, as in v1. BAY_DEPTH stays 38.
- **Cable cutouts**: ovals (stadiums, full round ends) 28 × 16, like every
  cable hole in the dock (revision 2026-09-24), one at each bay's outer end; the
  Ion bay keeps three along its length (UNDERSIDE_PORT_CUTOUTS). They sit
  within each bay's floor, clear of the sloped wall.
- **Fixed internal walls**: the centre partition and the two right-column
  dividers are fused to the plate and outer walls, full bay depth, WALL (2.0)
  thick. There are no rail slots and no RAIL_WALL thickening.
- **Rounding**:
  - R6 on every vertical inside corner, where internal walls meet each other
    or an outer wall.
  - R3 where every wall meets the bay floor.
  - R0.8 on the top edge of every internal wall, not a full round: a full
    round of a WALL-thick (2.0 mm) top would leave no flat face to fillet
    from.

  All of these face up or sideways, so the chamfer-on-downward-edges rule
  does not apply.
- **Lift-out**: a finger slot through the centre partition near its top,
  about 25 wide × 15 tall with a pointed-arch (45°) head so it prints
  unsupported. It replaces the rim notches.

## Base

Prints open-top-up with no supports (revision 2026-09-24: the cord port became an oval whose flat top bridges).

- **Shell**: a single WALL (2.0) sloped wall and a FLOOR (1.2) floor. This
  replaces v1's 2·WALL lower walls, which existed only to carry the rebate
  ledge.
- **Tray ledge**: a continuous ring on the inner wall at the tray's floor
  depth that the tray rests on. It stands 3.0 mm proud of the wall
  (LEDGE_W) and is chamfered underneath, so it prints unsupported. The tray
  rim sits TRAY_SINK = 0.3 below the base rim, so the lid lands on the base. The tray's outer wall
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
- **Cord port**: a 26 × 16 oval (stadium, R8 ends) through the −X wall,
  centred on the inlet (revision 2026-09-24; was a rectangle printed on
  supports). A figure-8 (C7) end of CORD_END size passes; its 10 mm flat top
  bridges.
- **Escape ports**: two stadium-shaped holes (nearly oval, up to 14 × 8 with
  full R4 ends) in the −X wall, one each side of the fence. Each is centred
  in Y in the gap between the fence and the side wall, with its sill above
  the colour groove (sill at `BAND_H + GROOVE_UP + 1.5`, i.e. 10.4). This
  replaces the single port above the cord port, which the charger's height
  covered. Each port's length (ESCAPE_L) is derived, capped at 14, so a full
  WALL of material remains to both the fence and the corner arc at that
  height. Their flat heads (ESCAPE_L − ESCAPE_H, up to 6 mm at the cap) are
  short bridges.
- **Cable drop**: the cutouts at the bays' outer ends sit over the leaning
  wall, so a cable falls clear for at least 15 mm below the tray and then
  follows the wall down. v1's rule (clear all the way to the cavity floor)
  cannot hold with a 15° wall. The inner Ion cutouts drop clear to the floor.
- **Tie grid and feet**: the tie-down grid (Ø4 on a 24 mm pitch) and the
  four foot recesses stay, re-fitted to the smaller tapered floor.
- **Rim**: plain WALL rim, with no rebate and no notches.
- **Hinge knuckles**: see below.

## Hinge

Snap-on, no hardware. It sits on the +Y long side, at two stations about
60 mm in from each end. Revision 2026-09-24: hooks, cheeks and heel 3× wider
(HOOK_W 24, CHEEK_W 12, HEEL_W 24) for strength; mouths face straight down
with the lid closed; round bores; a lighter snap; OPEN_DEG 100.

- **Axis**: runs along X at rim height, far enough behind the rim
  (AXIS_Y) that the knuckles' swing clears the tray. Every knuckle turns
  inside a relief disc (RELIEF_R) cut out of the other part, and the discs
  are round the axis, so they stay clear at any angle.
- **Base**: each station has two cheeks with a horizontal Ø5 pin between
  them. Each cheek is a disc round the axis hulled with a 45° chin that runs
  into the wall, so it prints without supports. The pin's underside is cut
  flat at 0.8·r, which keeps the pin inside the bore circle. The flat is
  3 mm wide and bridges the ~25 mm hook gap (base.LONG_BRIDGES).
- **Lid**: a C-hook at each station. It is a ring round the pin with a
  plain round bore (0.4 mm clearance), hulled up into the lid's back wall
  and top. Its mouth faces straight down with the lid closed: a neck
  narrower than the pin by SNAP (0.2 mm, a light snap; clearance and snap
  are tuned on the hinge coupon), flaring open beyond the neck. The lid
  presses straight down onto the pins and lifts straight off. As printed
  (top face down) the mouths face up, so the bores print on supports.
- **Heel stop**: a separate 24 mm tab on the lid at X = 0, between the
  stations. At OPEN_DEG (100°) its tip rests on the base's outer wall, so
  the lid stays open. The angle is kept short of 110° because, resting on
  the heel, the lid pushes its hooks forward -- close to the mouths'
  direction once open -- and the further it leans back the harder the push.
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
  time and grams.
- **Measured during planning** (scratch build, slice_report.py, 0.20, PETG;
  v1 through the same script: 14 h 00 m / 582 g):

  | Thicknesses | Time | Grams |
  |---|---|---|
  | 2.0 plates, 2.4 walls (first draft) | 12 h 14 m (−13 %) | 508 (−13 %) |
  | 1.2 plates, 2.4 walls | 10 h 48 m (−23 %) | 450 (−23 %) |
  | **1.2 plates, 2.0 walls (chosen)** | **9 h 53 m (−29 %)** | **412 (−29 %)** |

  The solid plates and walls dominate what the slicer lays down, so the
  chosen set is WALL 2.0, FLOOR / TRAY_PLATE / LID_PLATE 1.2; THIN_WALL
  stays 1.6. The 0.28 mm draft layer for the base and lid is reported
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
- **Two-tone cost**: the prime/wipe tower is off for the single tool change,
  and docs/printing.md says so. The slice report slices single-colour, so it
  does not count the one tool change (about a minute).
- **Tests** (pytest, all measuring the built solids):
  - **Taper**: the outline sampled at several heights leans 15° ± 0.5°; the
    corner radius is ≈ R30 at the rim and ≈ R8 at the foot.
  - **Walls**: wall thickness ≥ WALL everywhere, including around both
    escape ports and the cord port.
  - **Tray fit**: seated on the ledge, the tray does not intersect the base,
    its rim is flush within 0.5 mm, and every bay floor holds its device
    plus the specified clearance.
  - **Lid**:
    - it lies flush on the rim;
    - swept from 0° to just short of OPEN_DEG it intersects neither the
      base nor the seated tray;
    - past OPEN_DEG the heel meets the wall;
    - lifted straight up while closed, the neck snaps over the pins and
      the lid comes off.
  - **Printability**: no downward face past 45°, with these allowlisted:
    - base: bridges of 20 mm or less (the ports' flat heads, foot recesses),
      and the hinge pins' flats across the hook gap (LONG_BRIDGES); no
      supports;
    - lid: the hook bores and mouths, no wider than a hook (printed on
      supports);
    - tray: none (the finger slot is a 45° arch).
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
