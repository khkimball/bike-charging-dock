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
    """A flat six-port desktop charger, lying on its back.

    All six ports are in one row on a single face; the AC inlet is on the
    opposite face.  So the *long* horizontal dimension is the port face, and
    the short one is the port-face-to-inlet-face distance.
    """
    port_face_width: float      # long face carrying the six ports
    port_to_inlet: float        # port face to the opposite (AC inlet) face
    height: float               # charger thickness when lying flat
    port_face_margin: float     # charger edge to first port centre, along the
                                # port face
    port_pitch: float           # centre to centre, adjacent ports in the row
    inlet_center_z: float       # AC inlet centre height above charger bottom
    # Port 1's centre to the LED centre, along the port face and away from
    # the other ports.  None on a charger with no status LED at all, which is
    # what tells the base to leave its +X end wall blind.
    led_offset_from_ports: float | None = None
    # Radius of the body's rounded vertical edges, seen from above: the
    # charger pocket's corners follow it.  See docs/measuring.md.
    corner_r: float = 6.0


# PUBLISHED Wahoo ROAM 3 spec (96 x 53 x 24 mm, 109 g), lying flat in its bay.
ROAM = Slab(length=96.0, width=53.0, thickness=24.0)
# PUBLISHED Trek/Bontrager spec (102.5 x 34.7 x 30.2 mm body), lying flat on
# its wide face: 34.7 mm wide, 30.2 mm tall.
ION = Slab(length=102.5, width=34.7, thickness=30.2)
# PUBLISHED-ish TRACKR RADAR (89.9 x 37.1 x 29.1 mm); conflicting sources,
# verify with calipers.
TRACKR = Slab(length=89.9, width=37.1, thickness=29.1)
# PUBLISHED Anker 112 W six-port desktop charger (A2154): 77 x 82 x 33 mm,
# 302 g, three USB-C and three USB-A in one row on the front face, AC inlet
# centred on the back face, and no status LED anywhere.  The port pitch is
# not published, so it is NOMINAL 12.5 with the row centred on the face
# (margin = (77 - 5 * 12.5) / 2 = 7.25), and so is the inlet height, taken as
# half the body.  The inlet's connector type is unconfirmed, so CORD_END
# below stays a C7 until someone looks at the back of the charger.
CHARGER = Charger(port_face_width=77.0, port_to_inlet=82.0, height=33.0,
                  port_face_margin=7.25,     # NOMINAL, from the pitch
                  port_pitch=12.5,           # NOMINAL A2154
                  inlet_center_z=16.5,       # NOMINAL, height / 2
                  led_offset_from_ports=None,   # the A2154 has no LED
                  corner_r=6.0)                 # NOMINAL until measured
# The moulded end of the mains cord -- an IEC C7 "figure of 8" connector --
# measured across the two lobes (width), across the flats (height) and along
# the cord axis (length).  This is what the base's cord port has to pass, so
# the port is sized from it; see docs/measuring.md.
CORD_END = Plug(width=24.0, height=14.0, length=30.0)         # NOMINAL C7
