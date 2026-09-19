"""Three device cradles. Each is printable standalone for fit testing.

Conventions shared by all three:
  * the print-bed face lies at Z = 0 and nothing dips below it,
  * the footprint is centred on the origin in X and Y,
  * the bottom outer outline is chamfered by `params.CHAMFER` (chamfers, never
    fillets, on downward-facing edges),
  * the device's cable comes up through the bed face, so a rectangular
    through-slot runs through the floor.  For a device whose port faces down
    the slot takes the plug overmold itself, sized plug + CLR_DEVICE per side,
    and a plug pushed up from below sits captive with its tip proud of the
    pocket floor.  The bottom-port Roam is the exception: its plug lies flat
    in a trough and only the cable drops through the bed face.  Retaining the
    plug is the deck's job (it carries a plug well under each slot), not the
    cradle's.
"""
import math

from build123d import (Align, Box, Cylinder, Part, Plane, Polyline, Pos, Rot,
                       chamfer, extrude, make_face)

from dock import measurements as M
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

ROAM_TILT = 20.0   # degrees, shelf tips toward the user (-Y)
# Gap between the pocket's bottom (-Y) wall face and the near edge of the
# plug slot, so the slot opens entirely inside the pocket floor.
ROAM_PORT_INSET = 1.0
# Vertical face at the thin front of the Roam wedge: without it the wedge
# would run out to a zero-height knife edge that cannot print and cannot
# take a chamfer.
ROAM_TOE = 2.0
ION_RING_H = 25.0  # ring height above its floor
ROAM_POCKET_FRACTION = 0.6
TRACKR_POCKET_FRACTION = 0.6
# Bottom-port Roam only: the plug lies in an open trough in front of the
# pocket wall and its tip reaches through the wall into the device.
ROAM_TROUGH_RUN = P.USB_C_PLUG.length + 2.0   # trough length along the floor
ROAM_TROUGH_W = P.USB_C_PLUG.width + 2 * P.CLR_DEVICE
ROAM_TROUGH_H = P.USB_C_PLUG.height + 2 * P.CLR_DEVICE
# ... and the cable drops to the bed face through a slot at the far end.
ROAM_CABLE_L = P.USB_C_CABLE.height + 2 * P.CLR_DEVICE   # slot run, along the trough
ROAM_CABLE_END_GAP = 1.0   # slot set back this far from the trough's front wall


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
    """Tilted shelf holding the lower 0.6 of the Roam face-up, open at +Y.

    With `ROAM.port_face == "bottom"` (the Wahoo Roam 3) the floor is left
    solid and the USB-C plug arrives horizontally: a plug-sized channel
    pierces the pocket's low (-Y) wall at floor level, an open trough in the
    nose ahead of that wall carries the overmold, and a slot at the trough's
    far end drops the cable to the bed face.  The channel's only ceiling is
    the 2.4 mm wall itself -- a WALL-span bridge.

    With `port_face == "back"` the original bore through the pocket floor is
    used instead, and there is no nose.
    """
    c = P.CLR_DEVICE
    pw = M.ROAM.width + 2 * c                          # pocket width (X)
    pl = M.ROAM.length * ROAM_POCKET_FRACTION + c      # pocket run up the slope
    pd = M.ROAM.thickness + 2 * c                      # pocket depth into the shelf
    ow, ol, oh = pw + 2 * P.WALL, pl + P.WALL, pd + P.FLOOR

    bottom_port = M.ROAM.port_face == "bottom"
    # nose ahead of the -Y wall that hosts the trough, plus its own front wall
    nose = ROAM_TROUGH_RUN + P.WALL if bottom_port else 0.0

    shelf = Box(ow, ol, oh, align=_MIN)
    # pocket walled on three sides, open at the +Y (upper) end and at +Z
    shelf -= Pos(0, P.WALL / 2, P.FLOOR) * Box(pw, pl, pd, align=_MIN)

    wall_out_y = -ol / 2            # outer face of the pocket's -Y wall
    wall_in_y = wall_out_y + P.WALL  # its inner face
    nose_front_y = wall_out_y - nose

    if bottom_port:
        shelf += Pos(0, (nose_front_y + wall_out_y) / 2, 0) * Box(
            ow, nose, P.FLOOR + ROAM_TROUGH_H, align=_MIN)
        # channel through the wall: closed, so its ceiling is a WALL bridge
        shelf -= Pos(0, (wall_out_y + wall_in_y) / 2, P.FLOOR) * Box(
            ROAM_TROUGH_W, P.WALL + 0.02, ROAM_TROUGH_H, align=_MIN)
        # open-top trough in the nose, continuing the same axis
        shelf -= Pos(0, (nose_front_y + P.WALL + wall_out_y) / 2, P.FLOOR) * Box(
            ROAM_TROUGH_W, ROAM_TROUGH_RUN + 0.01, P.THRU, align=_MIN)

    # Tilt toward -Y so the shelf floor normal tips at the user, then lift so
    # the lowest point of the underside sits ROAM_TOE above the bed.
    t = math.radians(ROAM_TILT)
    y_lo_local, y_hi_local = nose_front_y, ol / 2
    place = Pos(0, 0, ROAM_TOE - y_lo_local * math.sin(t)) * Rot(ROAM_TILT, 0, 0)
    part = place * shelf

    # Ramp fills the space under the tilted shelf; its sloped top *is* the
    # shelf underside (20 deg from horizontal -> no overhang past 45 deg).
    part += _wedge(ow, y_lo_local * math.cos(t), y_hi_local * math.cos(t),
                   (y_hi_local - y_lo_local) * math.sin(t), ROAM_TOE)

    if bottom_port:
        # Cable slot: vertical, at the trough's far end, dropping to the bed.
        y_cable = (nose_front_y + P.WALL + ROAM_CABLE_END_GAP
                   + ROAM_CABLE_L / 2)
        part -= (Pos(0, y_cable * math.cos(t) - P.FLOOR * math.sin(t), 0)
                 * P.plug_cutter(P.USB_C_CABLE))
    else:
        # Slot normal to the shelf floor, ROAM_PORT_INSET clear of the
        # pocket's bottom wall.  Cut after the union so it runs through shelf
        # and ramp alike, out to the bed.
        y_slot = (wall_in_y + ROAM_PORT_INSET
                  + (P.USB_C_PLUG.height + 2 * c) / 2)
        part -= place * Pos(0, y_slot, 0) * P.plug_cutter(P.USB_C_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))


def build_ion_cradle() -> Part:
    """Ring standing the Ion on its port end, micro-USB slot off-axis."""
    c = P.CLR_DEVICE
    inner_r = M.ION.diameter / 2 + c
    outer_r = inner_r + P.WALL

    part = Cylinder(outer_r, ION_RING_H + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Cylinder(inner_r, ION_RING_H, align=_MIN)
    part -= Pos(M.ION.port_offset_from_axis, 0, 0) * P.plug_cutter(P.MICRO_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))


def build_trackr_cradle() -> Part:
    """Upright pocket, the Trackr standing on its port end."""
    c = P.CLR_DEVICE
    pw = M.TRACKR.width + 2 * c
    pt = M.TRACKR.thickness + 2 * c
    depth = M.TRACKR.length * TRACKR_POCKET_FRACTION

    part = Box(pw + 2 * P.WALL, pt + 2 * P.WALL, depth + P.FLOOR, align=_MIN)
    part -= Pos(0, 0, P.FLOOR) * Box(pw, pt, depth, align=_MIN)
    part -= P.plug_cutter(P.USB_C_PLUG)

    return _sit_on_bed_centred(_chamfer_bottom_outline(part))
