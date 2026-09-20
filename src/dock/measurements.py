"""Caliper measurements. EDIT THESE after measuring the real objects.
All mm. Defaults are nominal/published values, marked NOMINAL."""
from dataclasses import dataclass

from dock.params import Plug


@dataclass(frozen=True)
class Slab:
    """A device lying face-up in a bay: length along the bay, width across
    it, thickness = height above the bay floor."""
    length: float     # longest dimension, along the bay
    width: float       # across the bay
    thickness: float   # height above the bay floor


@dataclass(frozen=True)
class Charger:
    """Anker PowerPort 6, lying flat.

    The six USB-A ports are all on one long face; the C7 inlet is on the
    opposite long face.  So the *long* dimension is the port face, and the
    short horizontal dimension is the port-face-to-inlet-face distance.
    """
    port_face_width: float      # long face carrying the six USB-A ports
    port_to_inlet: float        # port face to the opposite (C7 inlet) face
    height: float               # charger thickness when lying flat
    port_face_margin: float     # charger edge to first port centre, along the
                                # port face
    inlet_center_z: float       # C7 inlet centre height above charger bottom
    led_offset_from_ports: float  # port 1's centre to the LED centre, along
                                  # the port face, away from the other ports


# PUBLISHED Wahoo ROAM 3 spec (96 x 53 x 24 mm, 109 g), lying flat in its bay.
ROAM = Slab(length=96.0, width=53.0, thickness=24.0)
# PUBLISHED Trek/Bontrager spec (102.5 x 34.7 x 30.2 mm body), lying flat on
# its wide face: 34.7 mm wide, 30.2 mm tall.
ION = Slab(length=102.5, width=34.7, thickness=30.2)
# PUBLISHED-ish TRACKR RADAR (89.9 x 37.1 x 29.1 mm); conflicting sources,
# verify with calipers.
TRACKR = Slab(length=89.9, width=37.1, thickness=29.1)
CHARGER = Charger(port_face_width=96.0, port_to_inlet=65.0, height=26.0,
                  port_face_margin=10.0, inlet_center_z=13.0,
                  led_offset_from_ports=8.0)                  # NOMINAL A2123
# The moulded end of the mains cord -- an IEC C7 "figure of 8" connector --
# measured across the two lobes (width), across the flats (height) and along
# the cord axis (length).  This is what the base's cord port has to pass, so
# the port is sized from it; see docs/measuring.md.
CORD_END = Plug(width=24.0, height=14.0, length=30.0)         # NOMINAL C7
