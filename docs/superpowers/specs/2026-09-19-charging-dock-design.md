# Cycling Electronics Charging Dock — Design Spec

Date: 2026-09-19
Status: approved in brainstorming, pending spec review

## Goal

A desktop charging dock, in the spirit of the Trek CHRGtime, that hides a
multi-port USB charger and its cables and presents tidy cradles for three
specific devices plus one spare bay. Printed in PETG on a Snapmaker U1.

## Devices

| Device | Port | Charging posture |
|---|---|---|
| Wahoo Elemnt Roam 3 | USB-C (rear) | Face-up on a sloped shelf, cable rises through a slot behind it |
| Bontrager Ion Pro RT | Micro-USB (bottom) | Standing upright in a ring; cable rises from below into the port |
| Wahoo Trackr tail light | USB-C | Upright in a small pocket, cable rises from below |
| Spare bay | any | Open bay with a removable divider; cable through a floor slot |

All device pocket dimensions come from caliper measurements the user takes
(measurement list is a deliverable of the plan). Nothing is guessed from
marketing photos.

## Power

One desktop-style GaN charger with a detachable AC cord (not a wall-plug
brick), 4 ports minimum, at least 1 USB-A for the Ion Pro RT micro cable.
Default target: UGREEN Nexode 65W 4-port desktop charging station. The
charger cavity is fully parametric (L x W x H plus port-face side), and the
user measures the actual charger before the base is printed. Port face
points toward the cable channels; AC cord exits the rear through a notch.

## Geometry

Two printed pieces:

1. **Base tray** — holds the charger in a friction-fit cavity with a
   fingernail relief for removal, AC cord notch at the rear, rear "escape
   port" slot (a spare cable can leave the box to charge something on top),
   four rubber-foot recesses underneath. Open top.
2. **Deck** — sits on the base with a 0.2 mm lip fit and locates on
   corner pegs. Contains the three cradles and the spare bay. Underside has
   snap-in cable channels from each charger port to each cradle's floor
   slot. Each floor slot is sized for the cable's connector overmold plus
   0.3 mm so the plug sits captive with its tip proud of the floor.

Dividers: a single 2 mm slab with dovetail rails that drop into slots along
the spare bay walls.

Design rules:
- Wall thickness 2.4 mm (3 perimeters at 0.4 mm), floors 1.6 mm.
- Chamfers instead of fillets on downward-facing edges; no overhang past
  45 degrees without a designed-in support feature.
- Clearances: 0.3 mm device pockets, 0.2 mm deck-to-base, 0.25 mm divider
  rails. All tunable from one params block, calibrated by a fit coupon.
- Overall footprint target under 250 x 120 mm so it fits the U1 bed with
  margin; enforced by a test.

## Toolchain

- Python 3 venv in this repo: `build123d`, `ocp-vscode` (live browser
  viewer), `pytest`.
- `src/dock/params.py` — every dimension, with docstrings.
- `src/dock/base.py`, `src/dock/deck.py`, `src/dock/divider.py`,
  `src/dock/coupon.py` — one build function each returning a build123d
  Part.
- `src/dock/export.py` — writes STL, 3MF, STEP into `out/` (gitignored).
- `tests/` — bounding box, wall thickness sanity, pocket-to-device
  clearance, deck/base fit, bed-size limit.
- Slicer: OrcaSlicer (Flatpak) with the Snapmaker U1 PETG profile; the
  user slices and prints.

Onshape is not used. STEP export exists in case it is wanted later.

## Iteration sequence

1. Toolchain up, calibration coupon printed, clearances set from results.
2. User measures devices and charger; params filled in.
3. Cradle-only test prints (each cradle as a small standalone part).
4. Full deck, then base. Fit check, tune, reprint.

## Out of scope for v1

Lids, lighting, numbered stickers, Gridfinity compatibility, multi-material.
