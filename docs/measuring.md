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

## Anker A2154 112 W six-port charger (`CHARGER`)
Published: 77 x 82 x 33 mm, 302 g; three USB-C and three USB-A in one row on
the front face; AC inlet centred on the back face; no status LED.  Lay the
charger flat, ports toward you.
- port_face_width: the long horizontal dimension -- the face carrying the
  six ports
- port_to_inlet: the other horizontal dimension, port face to inlet face.
  Measure the back face to the port face *including anything proud of the
  back* -- an inlet shroud, a moulded label boss, a raised badge.  The base
  backs the charger onto the cavity's end wall and leaves
  `base.POCKET_BACK_SLACK` (2 mm) of free X behind it for exactly that; if
  what stands proud of the back is more than that, raise the slack rather
  than fudging this measurement.
- height: the remaining (vertical) dimension with the charger lying flat
- port_face_margin: charger edge to centre of the first port, measured along
  the port face
- port_pitch: centre to centre between adjacent ports.  Measure port 1 to
  port 6 and divide by five rather than measuring one gap -- five gaps share
  the error out.  Anker does not publish it; the file has a NOMINAL 12.5 with
  the row centred on the face, which is where `port_face_margin` comes from
  too.  The base's cable loops sit one per port on this pitch, so it is worth
  getting right.  A loop is `LOOP_W_IN + 2 * LOOP_T` = 16 mm wide, so the
  posts left between two windows are `port_pitch - LOOP_W_IN`: if the
  measured pitch comes in under **12.4 mm**, drop `base.LOOP_W_IN` to keep
  those posts at least `WALL` (2.4 mm) thick.  There is a test that fails if
  you forget.
- inlet_center_z: bottom of charger to centre of the AC inlet.  NOMINAL is
  half the body height.  The base's cord port has to span this, and the port
  narrows into a 45 degree peak above its rectangular part, so an inlet
  higher than expected is a real failure -- `test_base.py` measures it.
- led_offset_from_ports: `None` when the charger has no status LED.  The
  A2154 has none, and the base then cuts no window and leaves its +X end
  wall blind.  If yours does have one, measure from port 1's centre to the
  LED centre along the port face, *away* from the other ports: the LED sits
  at the end of the row, outboard of port 1, not between the ports.
- Check what the AC inlet actually is while you have the charger in hand.
  `CORD_END` below is still sized for an IEC C7 "figure of 8"; a C13 or C5
  inlet is a different shape and the cord port must be resized from it.

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
- Nothing is cut to these: every bay gets the same cable cutout
  (`tray.CUTOUT`, 28 x 16 through the plate). They are the check that the
  cutout is big enough -- if a remeasured overmold outgrows it, widen the
  cutout.
