"""Concealed leaf hinge, after the Trek CHRGtime's: the lid carries the pins,
the base the sockets.

Everything here is in base coordinates, with the lid modelled closed on the
rim; lid.py turns the lid over for printing and tray.py moves the tray's
recess into its own coordinates.  Two stations stand HINGE_INSET in from each
end of the +Y rim.

At each station:
- the base's back wall has a NOTCH_W notch cut down from the rim;
- the lid has a leaf hanging into it, flush with the base's outer wall (same
  draft), LEAF_T thick and reaching LEAF_L below the pivot.  From behind a
  closed dock shows only the leaf in its notch;
- Ø2*PIN_R pins stand PIN_L out of each leaf end along the axis, into
  sockets in blocks on the inside of the base wall beside the notch.  Each
  socket opens straight up through a neck SNAP narrower than the pin, so the
  lid presses down onto its pins and lifts off with a light snap;
- the axis is AXIS_DROP below the rim and AXIS_IN inside the outer face, so
  the lid's back edge would dip into the rim as it turns: the lid's back is
  raised BACK_GAP off the rim instead (back_relief);
- small lips on the socket blocks stop the leaf's ends at about OPEN_DEG.
  They are cut from the region the leaf's ends reach only after LIP_FROM_DEG
  of opening, less the leaf's path straight up (so the lid still lifts off),
  and tied to their blocks by risers beside the notch, where the leaf never
  goes;
- the tray's back wall steps in round the station (tray_recess) to give the
  leaf's swing and the lips room.

The socket blocks have 45-degree chins running into the wall, so the base
prints without supports.
"""
import math
from functools import lru_cache

from build123d import (Align, Axis, Box, Circle, Cylinder, Location, Part, Plane, Polygon,
                       Pos, Rectangle, Rot, Sketch, extrude, fillet, offset)

from dock import layout as L
from dock import params as P
from dock import taper

NOTCH_W = 30.0
SIDE_CLR = 0.5            # leaf end to notch side
NOTCH_GAP = 2.0           # below the leaf
NOTCH_R = 3.0             # notch bottom corners
AXIS_DROP = 4.0           # pivot below the rim
AXIS_IN = 3.5             # pivot inside the outer face
PIN_R = 3.0               # heavy duty: printed, not moulded
PIN_L = 5.0
BORE_CLR = 0.3            # tune on the hinge test print
BORE_R = PIN_R + BORE_CLR
SNAP = 0.3                # socket neck narrower than the pin; tune on the hinge test print
LEAF_T = 7.0              # from the outer face in
LEAF_L = 8.5              # below the pivot: long enough that the lips can reach it
LEAF_ROUND = 2.5          # leaf bottom edges
BLOCK_W = PIN_L + 3.0     # socket block along X
BLOCK_WALL = 2.5          # socket block round the bore
BACK_GAP = 1.5            # lid back edge off the rim
BACK_RELIEF_IN = 5.0      # ... from this far inside the pivot, so the back corners clear
LIP_W = 3.0               # lips reach this far into the notch from each end
LIP_R = 9.0               # and stay within this radius of the axis
LIP_CLR = 0.3
LIP_FROM_DEG = 94.0       # lips start where the leaf ends reach past this ...
OPEN_DEG = 101.0          # ... which stops the lid here (measured: tests/test_assembly.py)
RECESS_CLR = 0.5          # leaf swing to the tray's recess wall
HINGE_INSET = 60.0        # station centre in from each end of the rim

_RIM_Y = L.RIM.sy / 2
_H = L.BASE_H
AXIS_Z = _H - AXIS_DROP
STATIONS = (-(L.RIM.sx / 2 - HINGE_INSET), L.RIM.sx / 2 - HINGE_INSET)
_ALONG = (Align.CENTER, Align.CENTER, Align.MIN)


def y_out(z: float) -> float:
    """Y of the base's outer back face at height z."""
    return _RIM_Y - (_H - z) * taper.TAN


AXIS_Y = y_out(AXIS_Z) - AXIS_IN
_LEAF_TOP = _H + L.LID_H - P.LID_PLATE + 0.5   # up into the lid's top plate: no ledge inside the lid
_LEAF_BOT = AXIS_Z - LEAF_L
NOTCH_BOT = _LEAF_BOT - NOTCH_GAP


def x_cylinder(r: float, x0: float, x1: float) -> Part:
    """A cylinder of radius r round the hinge axis, from x0 to x1."""
    return Pos(x0, AXIS_Y, AXIS_Z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=_ALONG)


def opened(deg: float = 0.0) -> Location:
    """Turns a closed lid, in base coordinates, `deg` open about the axis."""
    return Pos(0, AXIS_Y, AXIS_Z) * Rot(-deg, 0, 0) * Pos(0, -AXIS_Y, -AXIS_Z)


def _prism(face: Sketch, x0: float, x1: float) -> Part:
    """A YZ face (sketched with X as Y and Y as Z) extruded along X."""
    return extrude(Plane.YZ.offset(x0) * face, amount=x1 - x0)


def _leaf_profile() -> list[tuple[float, float]]:
    return [(y_out(_LEAF_TOP), _LEAF_TOP), (y_out(_LEAF_TOP) - LEAF_T, _LEAF_TOP),
            (y_out(_LEAF_BOT) - LEAF_T, _LEAF_BOT), (y_out(_LEAF_BOT), _LEAF_BOT)]


def _turned(pts, deg: float) -> list[tuple[float, float]]:
    """`pts` (Y, Z) turned with the lid `deg` open."""
    a = math.radians(-deg)
    c, s = math.cos(a), math.sin(a)
    return [(AXIS_Y + (y - AXIS_Y) * c - (z - AXIS_Z) * s,
             AXIS_Z + (y - AXIS_Y) * s + (z - AXIS_Z) * c) for y, z in pts]


def _union(faces):
    out = None
    for f in faces:
        out = f if out is None else out + f
    return out


@lru_cache(maxsize=None)
def _lip_face() -> Sketch:
    """YZ section of a stop lip: where the leaf's ends go only past
    LIP_FROM_DEG, less where they go before it or on the way straight up."""
    prof = _leaf_profile()
    before = offset(_union(Polygon(*_turned(prof, d), align=None)
                           for d in range(0, int(LIP_FROM_DEG) + 1)), LIP_CLR)
    after = _union(Polygon(*_turned(prof, d), align=None)
                   for d in range(int(LIP_FROM_DEG) + 1, int(LIP_FROM_DEG) + 26))
    lifted = offset(_union(Polygon(*[(y, z + k * 0.5) for y, z in prof], align=None)
                           for k in range(0, 31)), LIP_CLR)
    ring = Pos(AXIS_Y, AXIS_Z) * Circle(LIP_R) - Pos(AXIS_Y, AXIS_Z) * Circle(PIN_R + 0.6)
    lip = ((after - before) - lifted) & ring
    lip = lip & (Pos(AXIS_Y, _H + 2.5) * Rectangle(80, 40, align=(Align.CENTER, Align.MAX)))
    return lip & (Pos(AXIS_Y, AXIS_Z) * Rectangle(40, 40, align=(Align.MAX, Align.CENTER)))


def _block_face(inner: float) -> Sketch:
    """YZ section of a socket block: from the wall in to `inner`, round the
    bore, with a 45-degree chin underneath running back into the wall so it
    prints without supports."""
    bottom = AXIS_Z - BORE_R - BLOCK_WALL
    # where the chin, running down-and-out at 45 degrees, meets the outer face
    z_w = (inner + bottom - _RIM_Y + _H * taper.TAN + 0.3) / (1 + taper.TAN)
    return Polygon((y_out(_H) - 0.3, _H), (inner, _H), (inner, bottom),
                   (inner + bottom - z_w, z_w), align=None)


def _ends(xs: float):
    """(sign, notch edge X) of a station's two ends."""
    return ((-1, xs - NOTCH_W / 2), (1, xs + NOTCH_W / 2))


def notches(stations=STATIONS) -> Part:
    """What the base's back wall gives up for the leaves."""
    part = None
    for xs in stations:
        n = Pos(xs, _RIM_Y - 6, NOTCH_BOT) * Box(NOTCH_W, 12, _H - NOTCH_BOT + 5, align=_ALONG)
        n = fillet(n.edges().filter_by(Axis.Y).group_by(Axis.Z)[0], NOTCH_R)
        part = n if part is None else part + n
    return part


def socket_blocks(stations=STATIONS) -> Part:
    """The socket blocks with their stop lips, to be added to the base."""
    lip = _lip_face()
    bb = lip.bounding_box()
    # the block reaches in under the lip's riser, so the chin carries both
    block_in = min(AXIS_Y - BORE_R - BLOCK_WALL, bb.min.X)
    riser = Pos(bb.min.X, _H - 0.5) * Rectangle(max(bb.max.X, block_in + 1.0) - bb.min.X,
                                                  bb.max.Y - (_H - 0.5), align=(Align.MIN, Align.MIN))
    part = None
    for xs in stations:
        for sgn, edge in _ends(xs):
            b0, b1 = sorted((edge, edge + sgn * BLOCK_W))
            l0, l1 = sorted((edge, edge - sgn * LIP_W))
            piece = _prism(_block_face(block_in), b0, b1) + _prism(lip + riser, b0, b1) + _prism(lip, l0, l1)
            part = piece if part is None else part + piece
    return part


def sockets(stations=STATIONS) -> Part:
    """Bore and upward snap neck for each pin, cut from the finished base."""
    part = None
    for xs in stations:
        for sgn, edge in _ends(xs):
            x0, x1 = sorted((edge - sgn * (SIDE_CLR + 0.01), edge + sgn * (PIN_L - SIDE_CLR + 0.5)))
            c = x_cylinder(BORE_R, x0, x1) + Pos((x0 + x1) / 2, AXIS_Y, AXIS_Z) * Box(
                x1 - x0, 2 * PIN_R - SNAP, 20, align=_ALONG)
            part = c if part is None else part + c
    return part


def leaves(stations=STATIONS) -> Part:
    """The leaves and their pins, closed position, to be added to the lid."""
    part = None
    for xs in stations:
        x0, x1 = xs - NOTCH_W / 2 + SIDE_CLR, xs + NOTCH_W / 2 - SIDE_CLR
        leaf = _prism(Polygon(*_leaf_profile(), align=None), x0, x1)
        leaf = fillet(leaf.edges().filter_by(Axis.X).group_by(Axis.Z)[0], LEAF_ROUND)
        leaf += x_cylinder(PIN_R, x0 - PIN_L, x0 + 0.5) + x_cylinder(PIN_R, x1 - 0.5, x1 + PIN_L)
        part = leaf if part is None else part + leaf
    return part


def back_relief() -> Part:
    """What the lid gives up along its back so its edge clears the rim."""
    return Pos(0, AXIS_Y - BACK_RELIEF_IN, _H - 1.0) * Box(
        L.RIM.sx + 20, 40, 1.0 + BACK_GAP, align=(Align.CENTER, Align.MIN, Align.MIN))


RECESS_Y = AXIS_Y - math.hypot(LEAF_T - AXIS_IN, LEAF_L) - 2 * RECESS_CLR
_RECESS_HW = NOTCH_W / 2 + BLOCK_W + 1.0


def tray_recess(stations=STATIONS) -> Sketch:
    """Plan (XY) of the region the tray gives up at the stations: back of
    RECESS_Y, over the hinge width, with 45-degree sides."""
    face = None
    for xs in stations:
        d = 30.0
        f = Polygon((xs - _RECESS_HW - d, RECESS_Y + d), (xs - _RECESS_HW, RECESS_Y),
                    (xs + _RECESS_HW, RECESS_Y), (xs + _RECESS_HW + d, RECESS_Y + d), align=None)
        face = f if face is None else face + f
    return face
