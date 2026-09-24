"""Lid: a shallow hinged cap that carries the base's taper up past the rim.

Its lower LID_SLOPE_H continues the base's 15 degree slope from the rim; its
top LIP_H is a lip standing LIP_W proud of that slope -- the finger grip for
opening it, and the reference's flared lid edge.  It sits on the rim with no
skirt: the hinge locates it.  Along the back it is raised hinge.BACK_GAP off
the rim, and it carries the hinge leaves (hinge.py).  Walls THIN_WALL, top
LID_PLATE.

It is modelled closed on the base, in base coordinates, which is where the
hinge pieces are built, then turned over about X (PRINT) to print top face
down: its walls lean inward as they rise from the bed, so nothing
overhangs but the leaf pins' undersides.  `lid_seat(deg)` puts the
printed part back on the base, `deg` open.
"""
from build123d import Location, Part, Plane, Pos, RectangleRounded, Rot, Sketch, extrude, loft

from dock import hinge as H
from dock import layout as L
from dock import params as P
from dock import taper

WALL_H = taper.horiz(P.THIN_WALL)
Z_RIM = L.BASE_H
Z_SLOPE = Z_RIM + L.LID_SLOPE_H
Z_TOP = Z_RIM + L.LID_H
LIP = L.RIM.at(Z_SLOPE, -L.LIP_W)              # (sx, sy, r) of the lip
PRINT = Pos(0, 0, Z_TOP) * Rot(180, 0, 0)      # closed on the base -> top face on the bed


def _rr(sx: float, sy: float, r: float, z: float) -> Sketch:
    return Plane.XY.offset(z) * RectangleRounded(sx, sy, r)


def _closed() -> Part:
    sx, sy, r = LIP
    c = P.CHAMFER
    body = L.RIM.solid(Z_RIM, Z_SLOPE)
    body += extrude(_rr(sx, sy, r, Z_SLOPE), amount=L.LIP_H - c)
    # the top edge is the bed edge as printed: chamfered, not filleted
    body += loft([_rr(sx, sy, r, Z_TOP - c), _rr(sx - 2 * c, sy - 2 * c, r - c, Z_TOP)])
    body -= L.RIM.solid(Z_RIM - 1.0, Z_TOP - P.LID_PLATE, inset=WALL_H)
    body -= H.back_relief()
    return body + H.leaves()


def build_lid() -> Part:
    return PRINT * _closed()


def lid_seat(deg: float = 0.0) -> Location:
    """Moves the printed lid onto the base, `deg` open."""
    return H.opened(deg) * PRINT.inverse()
