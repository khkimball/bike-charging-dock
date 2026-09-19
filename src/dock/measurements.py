"""Caliper measurements. EDIT THESE after measuring the real objects.
All mm. Defaults are nominal/published values, marked NOMINAL."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Slab:
    """A flat device measured lying face-up."""
    length: float     # longest dimension
    width: float
    thickness: float


@dataclass(frozen=True)
class Cylinder:
    """A round-bodied device standing on its charge-port end."""
    diameter: float
    length: float
    port_offset_from_axis: float  # micro-USB port centre distance from body axis


@dataclass(frozen=True)
class Charger:
    length: float               # port face to inlet face
    width: float
    height: float
    port_face_margin: float     # distance from charger edge to first port centre
    inlet_center_z: float       # C7 inlet centre height above charger bottom
    led_offset_from_ports: float  # LED centre distance from nearest port centre


ROAM = Slab(length=89.8, width=60.7, thickness=16.5)          # NOMINAL Wahoo spec
ION = Cylinder(diameter=32.0, length=100.0, port_offset_from_axis=6.0)  # NOMINAL guess
TRACKR = Slab(length=60.0, width=28.0, thickness=17.0)       # NOMINAL guess
CHARGER = Charger(length=96.0, width=65.0, height=26.0,
                  port_face_margin=10.0, inlet_center_z=13.0,
                  led_offset_from_ports=8.0)                  # NOMINAL A2123
