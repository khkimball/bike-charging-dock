"""Clearance calibration coupon: one plate with 6 graded holes, one peg."""
from build123d import Box, Pos, Part, Align

CLEARANCES = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4)
PEG = 10.0
PITCH = 16.0
THICK = 4.0


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
