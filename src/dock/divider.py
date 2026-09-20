"""Removable divider: 2 mm slab with a rectangular rail on each vertical edge.

It prints standing on its bottom edge, rails acting as feet, so that edge is
a downward edge and gets a chamfer (never a fillet).  The chamfer doubles as
elephant-foot relief: a squashed first layer on a hand-fitted part is what
stops it dropping the last half-millimetre into its rail slots.
"""
from build123d import Align, Axis, Box, Part, Pos, chamfer
from dock import params as P

THICK = 2.0
RAIL_W = 4.0   # rail width (Y), wider than the slab so it can't pull out sideways
RAIL_D = 2.0   # rail depth into the wall (X)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def build_divider(*, height: float, width: float,
                  bottom_chamfer: float = 0.5) -> Part:
    """Slab of `width` between the rail roots, `height` tall.

    `width` is the slab, not the overall part: each rail adds RAIL_D beyond
    it.  Callers size the slab narrower than the bay by CLR_RAIL so it does
    not rub on the bay walls.

    `bottom_chamfer` breaks the bed edge all round; pass 0 for a square one.
    """
    slab = Box(width, THICK, height, align=_MIN)
    rail = Box(RAIL_D, RAIL_W, height, align=_MIN)
    part = (slab
            + Pos(width / 2 + RAIL_D / 2, 0, 0) * rail
            + Pos(-width / 2 - RAIL_D / 2, 0, 0) * rail)
    if bottom_chamfer > 0:
        part = chamfer(part.faces().sort_by(Axis.Z)[0].edges(), bottom_chamfer)
    return part


def rail_cutter(height: float) -> Part:
    """Slot for divider rail: X gets c (single bearing face on bay side), Y gets 2c (pull-out clearance)."""
    c = P.CLR_RAIL
    return Box(RAIL_D + c, RAIL_W + 2 * c, height, align=_MIN)
