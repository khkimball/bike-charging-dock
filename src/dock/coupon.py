"""Calibration coupons.

`build_coupon`: one plate with six graded holes and one peg, for the fit
clearances in params.py.

`build_hinge_coupon`: one hinge station on a short stretch of wall and of
lid, for BORE_CLR and SNAP in hinge.py.  Print both halves, snap the hook
onto the pin by pulling it along the mouth, and swing it: tune the numbers
there before the base and lid, which are the two longest prints.
"""
from build123d import Align, Box, Part, Pos, Rot

from dock import hinge as H
from dock import layout as L

CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)
PEG = 10.0
PITCH = 16.0
THICK = 4.0

HINGE_SPAN = H.HOOK_W + 2 * (H.SIDE_CLR + H.CHEEK_W) + 6.0
_WALL_BLOCK = (8.0, 22.0)     # depth into the dock, height: holds the cheeks' chins
_LID_BLOCK = 12.0             # depth of lid behind the hook


def build_coupon() -> tuple[Part, Part]:
    n = len(CLEARANCES)
    plate = Box(PITCH * n + 6, PITCH + 6, THICK, align=(Align.MIN, Align.MIN, Align.MIN))
    for i, c in enumerate(CLEARANCES):
        hole = Box(PEG + 2 * c, PEG + 2 * c, THICK, align=(Align.CENTER, Align.CENTER, Align.MIN))
        plate -= Pos(3 + PITCH * i + PITCH / 2, 3 + PITCH / 2, 0) * hole
    # orientation notch beside the tightest hole
    plate -= Pos(0, 0, 0) * Box(3, 3, THICK, align=(Align.MIN, Align.MIN, Align.MIN))
    peg = Box(PEG, PEG, THICK * 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return plate, peg


def build_hinge_coupon() -> tuple[Part, Part]:
    """(base side, lid side), each on the bed as it prints."""
    st = (0.0,)
    y_rim = L.RIM.sy / 2
    depth, height = _WALL_BLOCK
    wall = Pos(0, y_rim - depth, H.AXIS_Z - height) * Box(
        HINGE_SPAN, depth, height, align=(Align.CENTER, Align.MIN, Align.MIN))
    base_side = wall - H.base_relief(st) + H.base_knuckles(st)
    base_side = Pos(0, -y_rim, -(H.AXIS_Z - height)) * base_side
    top = H.AXIS_Z + L.LID_H
    plate = Pos(0, y_rim - _LID_BLOCK, H.AXIS_Z) * Box(
        HINGE_SPAN, _LID_BLOCK, L.LID_H, align=(Align.CENTER, Align.MIN, Align.MIN))
    lid_side = plate - H.lid_relief(st) + H.lid_hooks(st)
    lid_side = Pos(0, y_rim, top) * Rot(180, 0, 0) * lid_side      # hook side up, like the lid
    return base_side, lid_side
