"""Removable divider: 2 mm slab with a rectangular rail on each vertical edge."""
from build123d import Box, Pos, Part, Align
from dock import params as P

THICK = 2.0
RAIL_W = 4.0   # rail width (Y), wider than the slab so it can't pull out sideways
RAIL_D = 2.0   # rail depth into the wall (X)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def build_divider(height: float, width: float) -> Part:
    slab = Box(width, THICK, height, align=_MIN)
    rail = Box(RAIL_D, RAIL_W, height, align=_MIN)
    return slab + Pos(width / 2 + RAIL_D / 2, 0, 0) * rail + Pos(-width / 2 - RAIL_D / 2, 0, 0) * rail


def rail_cutter(height: float) -> Part:
    """Slot for divider rail: X gets c (single bearing face on bay side), Y gets 2c (pull-out clearance)."""
    c = P.CLR_RAIL
    return Box(RAIL_D + c, RAIL_W + 2 * c, height, align=_MIN)
