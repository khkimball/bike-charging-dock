"""Three device cradles. Each is printable standalone for fit testing.

Conventions shared by all three:
  * the print-bed face lies at Z = 0 and nothing dips below it,
  * the footprint is centred on the origin in X and Y,
  * the bottom outer outline is chamfered by `params.CHAMFER` (chamfers, never
    fillets, on downward-facing edges),
  * a rectangular through-slot sized to the device-end plug + CLR_DEVICE per
    side runs through the floor, so a plug pushed up from below sits captive
    with its metal tip proud of the pocket floor. Retaining the plug is the
    deck's job (it carries a plug well under each slot), not the cradle's.
"""
import math

from build123d import (Align, Box, Cylinder, GeomType, Part, Plane, Polyline,
                       Pos, Rot, chamfer, extrude, make_face)

from dock import measurements as M
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_THRU = 200.0      # slot box length; longer than any cradle, so it cuts clear

ROAM_TILT = 20.0   # degrees, shelf tips toward the user (-Y)
# Gap between the pocket's bottom (-Y) wall face and the near edge of the
# plug slot, so the slot opens entirely inside the pocket floor.
ROAM_PORT_INSET = 1.0
# Vertical face at the thin front of the Roam wedge: without it the wedge
# would run out to a zero-height knife edge that cannot print and cannot
# take a chamfer.
ROAM_TOE = 2.0
ION_RING_H = 25.0  # ring height above its floor
TRACKR_POCKET_FRACTION = 0.6


def _slot(plug: P.Plug) -> Part:
    """Through-slot for a plug overmold pushed up from below (Z-thru box)."""
    return Box(plug.width + 2 * P.CLR_DEVICE,
               plug.height + 2 * P.CLR_DEVICE,
               _THRU, align=_CTR)


def _chamfer_bottom_outline(part: Part, amount: float = P.CHAMFER) -> Part:
    """Chamfer the outer outline of the lowest face (the bed face)."""
    bottom = min(part.faces(), key=lambda f: f.center().Z)
    return chamfer(bottom.outer_wire().edges(), amount)


def _sit_on_bed_centred(part: Part) -> Part:
    """Drop the part onto Z=0 and centre its footprint on the origin."""
    bb = part.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2,
               -(bb.min.Y + bb.max.Y) / 2,
               -bb.min.Z) * part


def cradle_footprint(part: Part) -> tuple[float, float]:
    s = part.bounding_box().size
    return (s.X, s.Y)


def _wedge(width_x: float, y_low: float, y_high: float,
           rise: float, toe: float) -> Part:
    """Flat-bottomed ramp prism: `toe` tall at y_low, `toe + rise` at y_high.

    Built as a 2D profile extruded along X so the boolean is a simple prism
    union rather than a rotated-box subtraction.
    """
    profile = make_face(Polyline((y_low, 0.0), (y_high, 0.0),
                                 (y_high, toe + rise), (y_low, toe),
                                 close=True))
    solid = extrude(Plane.YZ * profile, amount=width_x)
    bb = solid.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2, 0, 0) * solid


def build_roam_cradle() -> Part:
    """Tilted shelf holding the lower half of the Roam face-up, open at +Y."""
    c = P.CLR_DEVICE
    pw = M.ROAM.width + 2 * c          # pocket width (X)
    pl = M.ROAM.length * 0.5 + c       # pocket holds the lower half
    pd = M.ROAM.thickness + 2 * c      # pocket depth into the shelf
    ow, ol, oh = pw + 2 * P.WALL, pl + P.WALL, pd + P.FLOOR

    shelf = Box(ow, ol, oh, align=_MIN)
    # pocket walled on three sides, open at the +Y (upper) end and at +Z
    shelf -= Pos(0, P.WALL / 2, P.FLOOR) * Box(pw, pl, pd, align=_MIN)

    # tilt toward -Y so the shelf floor normal tips at the user, then lift so
    # the low (-Y) corner sits ROAM_TOE above the bed
    tilt = Rot(ROAM_TILT, 0, 0)
    drop = (ol / 2) * math.sin(math.radians(ROAM_TILT))
    place = Pos(0, 0, drop + ROAM_TOE) * tilt

    tilted = place * shelf

    # ramp fills the space under the tilted shelf; its sloped top *is* the
    # shelf underside (20 deg from horizontal -> no overhang past 45 deg)
    half = (ol / 2) * math.cos(math.radians(ROAM_TILT))
    part = tilted + _wedge(ow, -half, half, 2 * drop, ROAM_TOE)

    # Slot normal to the shelf floor, ROAM_PORT_INSET clear of the pocket's
    # bottom wall. Cut after the union so it runs through shelf and ramp
    # alike, out to the bed.
    pocket_wall_y = -pl / 2 + P.WALL / 2          # inner face of the -Y wall
    y_slot = (pocket_wall_y + ROAM_PORT_INSET
              + (P.USB_C_PLUG.height + 2 * c) / 2)
    part -= place * Pos(0, y_slot, 0) * _slot(P.USB_C_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))


def build_ion_cradle() -> Part:
    """Ring standing the Ion on its port end, micro-USB slot off-axis."""
    c = P.CLR_DEVICE
    inner_r = M.ION.diameter / 2 + c
    outer_r = inner_r + P.WALL

    part = Cylinder(outer_r, ION_RING_H + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Cylinder(inner_r, ION_RING_H, align=_MIN)
    part -= Pos(M.ION.port_offset_from_axis, 0, 0) * _slot(P.MICRO_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))


def build_trackr_cradle() -> Part:
    """Upright pocket, the Trackr standing on its port end."""
    c = P.CLR_DEVICE
    pw = M.TRACKR.width + 2 * c
    pt = M.TRACKR.thickness + 2 * c
    depth = M.TRACKR.length * TRACKR_POCKET_FRACTION

    part = Box(pw + 2 * P.WALL, pt + 2 * P.WALL, depth + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Box(pw, pt, depth, align=_MIN)
    part -= _slot(P.USB_C_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))
