"""Calibration coupons.

`build_coupon`: one plate with six graded holes and one peg, for the fit
clearances in params.py.

`build_hinge_coupon`: one hinge station cut out of the real base and lid --
the notch, socket blocks and stop lips on a stretch of back wall, and the
leaf on a stretch of lid -- for BORE_CLR and SNAP in hinge.py and to try the
stop.  Print both halves, press the leaf's pins down into the sockets, and
swing it: tune the numbers there before the base and lid, which are the two
longest prints.
"""
from build123d import Align, Box, Part, Pos, Rot

from dock import base as B
from dock import hinge as H
from dock import layout as L
from dock import lid as LD

CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)
PEG = 10.0
PITCH = 16.0
THICK = 4.0

HINGE_SPAN = H.NOTCH_W + 2 * H.BLOCK_W + 8.0     # the coupon's length along the hinge
_COUPON_IN = 14.0                                  # how far into the dock it reaches


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
    xs = H.STATIONS[1]
    y0 = H.RECESS_Y - 1.0
    z0 = H.NOTCH_BOT - 6.0
    top = LD.Z_TOP
    box = Pos(xs, y0, z0) * Box(HINGE_SPAN, L.RIM.sy / 2 + 10 - y0, top - z0,
                                align=(Align.CENTER, Align.MIN, Align.MIN))
    base_side = Pos(-xs, -y0, -z0) * (B.build_base() & box)
    lid_box = Pos(xs, H.AXIS_Y - _COUPON_IN, z0) * Box(HINGE_SPAN, 40, top - z0,
                                                       align=(Align.CENTER, Align.MIN, Align.MIN))
    lid_side = LD._closed() & lid_box
    lid_side = Pos(-xs, 0, 0) * (LD.PRINT * lid_side)      # top face on the bed, like the lid
    return base_side, lid_side
