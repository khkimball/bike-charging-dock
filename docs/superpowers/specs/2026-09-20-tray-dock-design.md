# Charging Dock v2 — Tray Design Spec

Date: 2026-09-20
Status: approved in chat (supersedes the cradle deck of the 2026-09-19 spec)

## Why v2

The user showed the Trek CHRGtime reference: devices lie face-up in flat
rectangular bays, each bay has a small rectangular cable cutout at its outer
end that the plug comes up through, dividers are removable, the charger lives
underneath, the box has rounded vertical corners and a shallow lift-off style
cover. v1 stood devices upright in shaped cradles; that is replaced.

## Parts (three printed pieces, plus dividers)

1. **Base** — rounded-corner open box hiding the Anker PowerPort 6 and the
   cable slack. Top rebate receives the tray so the bay walls sit flush with
   the base rim. Charger fence, cord notch (−X end wall, open to the top),
   escape port (rear wall), LED window (+X end wall), foot recesses. The floor
   area beside the charger (the port side) carries a grid of 4 mm holes on a
   12 mm pitch for tying cable slack down, as in the reference teardown.
2. **Tray** — a plate with 2.4 mm walls forming four bays, 32 mm deep (BAY_DEPTH, ≥ tallest device + 1):
   - Left bay: Wahoo ROAM 3 lying face-up, long axis along Y, cable cutout at
     the front (−Y) end.
   - Right column, three bays stacked in Y, long axis along X, cable cutouts at
     the +X end: Bontrager Ion Pro RT (top, +Y), Wahoo TRACKR (middle), spare
     (bottom, −Y).
   - The two separators in the right column are removable dividers riding in
     rail slots on the partition wall and the +X outer wall, so bays can be
     merged. The left/right partition and the outer walls are fixed.
   - Each cable cutout is a rectangular through-hole in the plate, 22 × 12 mm,
     so the plug lies flat beside the device with the cable dropping into the
     base cavity.
   - Bay clearance: 3 mm per side around each device (bays, not pockets).
3. **Lid** — a shallow cap: 2.4 mm top plate with an 8 mm skirt that drops
   over the outside of the base top with CLR_FIT. Same rounded corners.
   Prints top-face-down. No hinge.
4. **Divider** — existing rectangular-rail slab, height = bay depth, width =
   bay width − CLR_RAIL.

## Geometry rules

- Vertical outer corners filleted R8 on base and lid; the tray's outer corners
  follow (R8 − WALL − CLR_FIT). Bay inner corners stay square.
- Wall 2.4, floor 1.6, tray plate 3.0. Chamfers on downward edges, no
  overhang past 45°, bridges ≤ 20 mm allowed.
- Clearances: CLR_FIT 0.15 (coupon, PLA), CLR_RAIL 0.20, CLR_BAY 3.0.
- Bed limit raised to 250 × 250 (U1 is 270 cube); target footprint about
  205 × 140 mm, base height about 75 mm.
- Base height = FLOOR + charger height + CABLE_ROOM 15 + tray height (plate +
  bay depth).
- Charger pocket: port_to_inlet + 2·CLR_FIT by port_face_width + 2·CLR_FIT,
  ports toward +X with 40 mm plug room, inlet toward −X. Cavity must clear the
  fence by ≥ 2 mm per side in Y; the tray's Y is driven by the bays, and the
  base grows only if the fence needs it.
- Measurements: ROAM 96 × 53 × 24 (published), ION 102.5 × 30.2 × 34.7
  (published; lying flat it is 34.7 wide × 30.2 tall), TRACKR 89.9 × 37.1 ×
  29.1 (published, conflicting), CHARGER nominal 96 × 65 × 26 until measured.
  The ION measurement becomes a Slab (length, width, thickness).

## Removed from v1

cradles.py and deck.py and their tests; the Cylinder measurement type; the
port_face/port_height fields (devices lie flat; the plug is horizontal in the
bay).

## Out of scope

Hinge, felt lining, lid latch, lettering, numbered stickers.
