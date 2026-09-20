# What to measure (digital calipers, mm, one decimal)

Enter each value in `src/dock/measurements.py`, then run `uv run pytest`.

Each device is a `Slab(length, width, thickness)`: it lies face-up flat in
its bay, `length` along the bay, `width` across it, `thickness` = height
above the bay floor.

## Wahoo Roam 3 (`ROAM`)
- length: top to bottom edge, at the widest, along the bay
- width: side to side at the widest, across the bay
- thickness: face to back, including the rear mount tabs -- how tall it
  stands above the bay floor
- Published values now in the file: `Slab(96.0, 53.0, 24.0)`.

## Bontrager Ion Pro RT (`ION`)
Lies flat on its side, not standing on its tail.
- length: lens face to tail, along the bay
- width: body diameter across the bay (34.7 mm)
- thickness: body diameter above the bay floor (30.2 mm) -- the Ion's body is
  not perfectly round, so width and thickness may differ slightly; use the
  cross-section as it actually rests
- Published values now in the file: `Slab(102.5, 34.7, 30.2)`.

## Wahoo Trackr (`TRACKR`)
- length, width, thickness of the body without the mount clip, lying flat
- Published values now in the file: `Slab(89.9, 37.1, 29.1)`.

## Anker PowerPort 6 (`CHARGER`)
Lay the charger flat, ports toward you.  The six USB-A ports are on one long
face; the C7 mains inlet is on the opposite long face.
- port_face_width: the long dimension -- the face carrying the six ports
- port_to_inlet: the short horizontal dimension, port face to inlet face
- height: the remaining (vertical) dimension with the charger lying flat
- port_face_margin: charger edge to centre of the first USB port, measured
  along the port face
- inlet_center_z: bottom of charger to centre of the C7 inlet
- led_offset_from_ports: distance from port 1's centre to the LED centre,
  measured along the port face *away* from the other ports.  The LED is at
  the end of the row, outboard of port 1, not between the ports.

## Mains cord end (`CORD_END`, a `params.Plug`)
The moulded end of the charger's mains cord -- an IEC C7 "figure of 8"
connector.  The base's cord port is sized from it, so measure the moulded
body, not the cable:
- width: across the two lobes, at the widest point of the moulding
- height: across the flats, the short way through the moulding
- length: along the cord axis, from the face that meets the inlet to where
  the moulding tapers back into the cable
A C7 end is nominally 24 x 14 mm; check yours, some are fatter.

## Cables (`params.py` Plug entries)
- For each cable: overmold width, height and length at the device end and
  the USB-A end. Update `USB_A_PLUG`, `USB_C_PLUG`, `MICRO_PLUG` with the
  largest of each.
- `USB_C_CABLE` is the bare cable just behind the overmold, not the overmold:
  it is what the Roam cradle's cable slot has to pass.
