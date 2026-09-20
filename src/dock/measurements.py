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
    port_height: float | None = None
    """Centre of the charge port above the face the device rests on, mm.

    The device lies back-down on the cradle floor, so this is measured from
    the back face to the port centre.  `None` means the port is on the
    device's mid-plane, i.e. `thickness / 2`.
    """

    @property
    def port_center_height(self) -> float:
        """`port_height`, defaulting to the device's mid-thickness."""
        return self.thickness / 2 if self.port_height is None else self.port_height


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
    led_offset_from_ports: float  # port 1's centre to the LED centre, along
                                  # the port face, away from the other ports


# Wahoo puts the Roam 3's USB-C on the bottom edge, so the cradle takes the
# plug in sideways through the pocket wall instead of boring its floor.
ROAM = Slab(length=96.0, width=53.0, thickness=24.0,
            port_face="bottom", port_height=None)            # PUBLISHED Wahoo ROAM 3 spec (96x53x24, 109 g); port_height still unmeasured
# PUBLISHED Trek spec: 102.5 x 30.2 x 34.7 mm body; it is not round, so the ring
# uses the larger cross-section dimension for now (slop of ~4.5 mm on the narrow axis).
ION = Cylinder(diameter=34.7, length=102.5, port_offset_from_axis=0.0)  # port offset unmeasured
# The Trackr already stands on its port end, so "bottom" costs it no geometry.
TRACKR = Slab(length=89.9, width=37.1, thickness=29.1,
              port_face="bottom")                            # PUBLISHED-ish TRACKR RADAR (37.1 x 89.9 x 29.1); conflicting sources, verify
CHARGER = Charger(port_face_width=96.0, port_to_inlet=65.0, height=26.0,
                  port_face_margin=10.0, inlet_center_z=13.0,
                  led_offset_from_ports=8.0)                  # NOMINAL A2123
