"""Lid: a shallow lift-off cap that drops over the outside of the base.

It is a WALL-thick top plate with an 8 mm skirt hanging off it, like the
overhanging cover on the reference dock: the skirt wraps the base's top
CLR_FIT clear on each side, so the lid locates itself as it is dropped on
and lifts straight off.  Nothing latches -- the skirt's depth is what keeps
it on.

The lid has its own origin, like every other part: it is built in print
orientation, plate face down on the bed, X = 0..LID_X, Y centred on 0, skirt
rising to Z = LID_H.  That way the only downward faces are the bed face and
the 45 degree chamfer around it, so it prints with no overhang and no bridge.
`lid_seat()` turns it over onto the base for assembly views and fit checks.

Three radii, all concentric: the base's outer corner is CORNER_R, the skirt's
inner corner is CORNER_R + CLR_FIT and its outer corner is
CORNER_R + WALL + CLR_FIT, so the gap round the base is uniform through the
corners as well as along the sides.

Chamfer, not fillet, on the plate's outer edge: printed plate-down that edge
is a downward edge.
"""
from build123d import Align, Axis, Box, Location, Part, Pos, chamfer, fillet

from dock import base as B
from dock import params as P

SKIRT_H = 8.0                           # how far the skirt reaches down the base
LID_H = P.V1_WALL + SKIRT_H                # plate plus skirt: the printed height

# The skirt clears the base by CLR_FIT per side and is WALL thick beyond that.
_OVER = P.V1_WALL + P.CLR_FIT
LID_X = B.BASE_X + 2 * _OVER
LID_Y = B.BASE_Y + 2 * _OVER
OUTER_R = P.V1_CORNER_R + _OVER            # concentric with the base's CORNER_R
INNER_R = P.V1_CORNER_R + P.CLR_FIT        # likewise
OPENING_X = B.BASE_X + 2 * P.CLR_FIT
OPENING_Y = B.BASE_Y + 2 * P.CLR_FIT

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _rounded_box(sx: float, sy: float, sz: float, r: float) -> Part:
    """A box centred in X and Y, up from Z, with its vertical edges filleted."""
    b = Box(sx, sy, sz, align=_MIN)
    return fillet(b.edges().filter_by(Axis.Z), r) if r > 0 else b


def lid_seat() -> Location:
    """Where `build_lid()` goes to sit on `base.build_base()`.

    Flips the printed lid over (180 degrees about X) and drops it on: the
    plate's underside lands on the base's rim at Z = BASE_H, its top face at
    BASE_H + WALL, and the skirt hangs SKIRT_H down the base's outside.  The
    lid is centred on the base footprint, which runs X = 0..BASE_X.
    """
    return Location((-_OVER, 0, B.BASE_H + P.V1_WALL), (180, 0, 0))


def build_lid() -> Part:
    """The lid, plate-down on the bed: X 0..LID_X, Y centred, Z 0..LID_H."""
    cx = LID_X / 2
    body = Pos(cx, 0, 0) * _rounded_box(LID_X, LID_Y, LID_H, OUTER_R)
    # The plate face is the bed face when printing, so its outer edge is a
    # downward edge: chamfer it, and do it before the skirt is hollowed out
    # so only the outer profile is touched.
    body = chamfer(body.faces().sort_by(Axis.Z)[0].edges(), P.CHAMFER)

    # Hollow out everything above the plate: what is left is the skirt.
    # Run the cutter past the rim for a clean top edge.
    body -= Pos(cx, 0, P.V1_WALL) * _rounded_box(
        OPENING_X, OPENING_Y, SKIRT_H + 1.0, INNER_R)
    return body
