"""Caliper measurements. EDIT THESE after measuring the real objects.
All mm. Defaults are nominal/published values, marked NOMINAL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Slab:
    """A flat device measured lying face-up."""
    length: float     # longest dimension
    width: float
    thickness: float
    port_face: str = "bottom"   # "bottom" (port on the bottom edge) or "back"


@dataclass(frozen=True)
class Cylinder:
    """A round-bodied device standing on its charge-port end."""
    diameter: float
    length: float
    port_offset_from_axis: float  # micro-USB port centre distance from body axis


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
    led_offset_from_ports: float  # LED centre to nearest port centre, along
                                  # the port face


# Wahoo puts the Roam 3's USB-C on the bottom edge, so the cradle takes the
# plug in sideways through the pocket wall instead of boring its floor.
ROAM = Slab(length=89.8, width=60.7, thickness=16.5,
            port_face="bottom")                              # NOMINAL Wahoo spec
ION = Cylinder(diameter=32.0, length=100.0, port_offset_from_axis=6.0)  # NOMINAL guess
# The Trackr already stands on its port end, so "bottom" costs it no geometry.
TRACKR = Slab(length=60.0, width=28.0, thickness=17.0,
              port_face="bottom")                            # NOMINAL guess
CHARGER = Charger(port_face_width=96.0, port_to_inlet=65.0, height=26.0,
                  port_face_margin=10.0, inlet_center_z=13.0,
                  led_offset_from_ports=8.0)                  # NOMINAL A2123
