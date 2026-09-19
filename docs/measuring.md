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
