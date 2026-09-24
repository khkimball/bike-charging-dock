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
  cable hole in the dock (revision 2026-09-24), one at each bay's outer end,
  the headlight bay included (revision 2026-09-24: the Ion's underside
  socket needed three along its bay; its replacement charges from the back,
  so the bay stays Ion-sized with one cutout at the end). They sit within
  each bay's floor, clear of the sloped wall.
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
- **Lift-out**: by the walls; no finger slot (removed in the 2026-09-24
  revision -- the tray pulls out easily by its walls).

## Base

Prints open-top-up; supports only under the four hinge socket blocks and their stop-lip risers (revision 2026-09-24b).

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
  - **Fillets along the charger's sides** (revision 2026-09-24): the
    A2154's long bottom edges are rounded, so the pocket floor meets its two
    side walls in a concave fillet of `Charger.edge_r` + CLR_FIT (NOMINAL
    until measured; see docs/measuring.md), capped below the fence top. No
    fillet on the front wall; all vertical corners square.
  - **Fused to the end wall** (revision 2026-09-24): the side arms run on
    into the leaning −X wall and are trimmed to the base's outside, so they
    join it along the angle at every height.
  - **Height = colour line** (revision 2026-09-24): FENCE_H = BAND_H − FLOOR,
    so the fence top is at 8.0 mm and the whole fence prints dark; the
    filament change goes at the first layer above 8.0.
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
  cannot hold with a 15° wall.
- **Tie grid and feet**: the tie-down grid (Ø4 on a 24 mm pitch) and the
  four foot recesses stay, re-fitted to the smaller tapered floor.
- **Rim**: plain WALL rim, with no rebate and no notches.
- **Hinge knuckles**: see below.

## Hinge

Revision 2026-09-24b: a concealed leaf hinge after the Trek CHRGtime's
(replacing the knuckle-and-hook hinge). Snap-on, no hardware, on the +Y long
side at two stations about 60 mm in from each end.

- **Notch**: at each station the base's back wall has a notch NOTCH_W
  (30) wide, from the rim down past the leaf with a 2 mm gap below it and
  rounded bottom corners.
- **Leaf**: the lid carries a leaf that hangs into the notch, flush with
  the base's outer wall (same 15° slope), 7 mm thick, reaching LEAF_L
  (8.5) below the pivot, its bottom edge rounded. Closed, the back of the
  dock shows only the leaf in its notch (as the reference).
- **Pins and sockets**: heavy-duty Ø6 pins stand out 5 mm from each leaf
  end along the hinge axis, into sockets in blocks on the inside of the
  base wall beside the notch. The sockets open upward through a neck
  SNAP (0.3) narrower than the pin, so the lid presses straight down onto
  its pins and lifts straight off with a light snap. The axis is 4 mm
  below the rim and 3.5 mm inside the outer face.
- **Back gap**: because the axis is inside the wall line, the lid's back
  edge would dip into the rim as it opens; the lid's back is raised 1.5 mm
  off the rim (BACK_GAP) along the back and round the back corners, as on
  the reference.
- **Stop**: small lips on the socket blocks catch the leaf's ends at about
  101° (OPEN_DEG). They sit only where the leaf's ends go past about 94°
  of opening, clear of both the swing before that and the leaf's path
  straight up when the lid is lifted off; each is tied to its block by a
  riser beside the notch, where the leaf never goes. The riser tops stand
  about 1 mm above the rim, inside the lid.
- **Tray recess**: the tray's back wall steps in around each hinge with
  45° sides (as the reference tray), vertical over the recess, so the
  leaf's swing and the lips have room. The headlight moves 3 mm forward in
  its bay (6 mm clear at the back, 5 mm to the divider) to clear the
  right-hand recess.
- **Printing**: the socket blocks and the lips' risers have flat undersides,
  printed on supports (the user's choice over 45° chins). The lid's leaf
  pins are short horizontal stubs as it prints top-down.
- **Hinge coupon**: one station cut from the real base and lid, to tune
  BORE_CLR and SNAP and to try the stop before the long prints.

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
    - it lies on the rim (front and sides; the back is raised BACK_GAP);
    - swept from 0° to just short of OPEN_DEG it intersects neither the
      base nor the seated tray;
    - just past OPEN_DEG the leaf meets the stop lips;
    - lifted straight up while closed, the neck snaps over the pins and
      the lid comes off.
  - **Printability**: no downward face past 45°, with these allowlisted:
    - base: downward faces of 20 mm or less (the ports' flat heads, foot
      recesses, and the socket blocks' and lip risers' undersides, which
      print on supports);
    - lid: the leaf pins' undersides;
    - tray: none.
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
