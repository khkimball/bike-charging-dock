# What to measure (digital calipers, mm, one decimal)

Enter each value in `src/dock/measurements.py`, then run `uv run pytest`.

## Wahoo Roam 3 (`ROAM`)
- length: top to bottom edge, at the widest
- width: side to side at the widest
- thickness: face to back, including the rear mount tabs
- port_face: `"bottom"` if the USB-C port is on the bottom edge (the Roam 3),
  `"back"` if it is on the rear face.  A bottom port gets a plug trough and a
  channel through the pocket wall; a back port gets a bore through the shelf
  floor instead.
- Also note the distance from the bottom edge to the USB-C port centre.

## Bontrager Ion Pro RT (`ION`)
- diameter: body diameter at the widest point
- length: lens face to tail
- port_offset_from_axis: with the light standing on its tail, distance from
  the body centre to the micro-USB port centre (0 if centred)

## Wahoo Trackr (`TRACKR`)
- length, width, thickness of the body without the mount clip
- port_face: the Trackr stands on its port end, so `"bottom"` is right and
  costs it no geometry; set `"back"` only if the port is on a face.

## Anker PowerPort 6 (`CHARGER`)
Lay the charger flat, ports toward you.  The six USB-A ports are on one long
face; the C7 mains inlet is on the opposite long face.
- port_face_width: the long dimension -- the face carrying the six ports
- port_to_inlet: the short horizontal dimension, port face to inlet face
- height: the remaining (vertical) dimension with the charger lying flat
- port_face_margin: charger edge to centre of the first USB port, measured
  along the port face
- inlet_center_z: bottom of charger to centre of the C7 inlet
- led_offset_from_ports: nearest port centre to LED centre, measured along
  the port face

## Cables (`params.py` Plug entries)
- For each cable: overmold width, height and length at the device end and
  the USB-A end. Update `USB_A_PLUG`, `USB_C_PLUG`, `MICRO_PLUG` with the
  largest of each.
- `USB_C_CABLE` is the bare cable just behind the overmold, not the overmold:
  it is what the Roam cradle's cable slot has to pass.
