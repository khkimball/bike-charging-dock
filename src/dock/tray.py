"""Tray: a flat plate with four bays for devices lying face-up.

Layout follows the Trek CHRGtime reference: one tall bay on the left for the
Wahoo ROAM lying long-axis-along-Y, and a column of three bays on the right
stacked in Y with their long axes along X.  Every bay has a rectangular cable
cutout through the plate at its *outer* end, so the plug lies flat beside the
device and the cable drops into the base cavity below.  The two separators in
the right column are removable dividers riding in rail slots cut into the
partition wall and the +X outer wall; the four outer walls and the partition
are fixed.

Tray coordinates: X runs 0..TRAY_X, Y is centred on 0, plate bottom at Z = 0.
Printed plate-down, bays up: nothing in the part overhangs.
"""
from build123d import Align, Axis, Box, Part, Pos, chamfer, fillet

from dock import divider as D
from dock import measurements as m
from dock import params as P

# Cable cutout through the plate: (along the bay, across the bay).  The run
# clears a USB-A overmold (P.USB_A_PLUG.length) laid flat with room behind it
# for the cable to bend; the width clears the same overmold across
# (P.USB_A_PLUG.width) once the plug is turned in line with the bay.
CUTOUT = (28.0, 16.0)   # v2.1: was 22 x 12, too tight once the cable bends
CUTOUT_INSET = 2.0   # cutout edge to the bay's end wall

# Bays whose device charges through a socket on its UNDERSIDE (the Ion Pro RT)
# get several cutouts spread along the bay, so the cable can drop straight
# down wherever the socket lands.  Other bays keep one cutout at the far end.
UNDERSIDE_PORT_CUTOUTS = {"ion": 3}

# Outer vertical corner radius: the tray drops inside the base's R8 corners.
OUTER_R = P.V1_CORNER_R - P.V1_WALL - P.CLR_FIT
# The -X bay void's corners are rounded concentric with the outer corner, so
# the shell keeps WALL on the diagonal -- the shortest line through a corner.
# A square void behind a rounded corner would leave only 1.1 mm there.
BAY_CORNER_R = OUTER_R - P.V1_WALL

# Walls carrying rail slots must keep WALL of material behind the slot.
RAIL_WALL = P.V1_WALL + D.RAIL_D + P.CLR_RAIL

# --- bay interiors -----------------------------------------------------------
# Left bay: ROAM lying face-up, long axis along Y, cutout at the -Y end.
_LEFT_W = m.ROAM.width + 2 * P.CLR_BAY
_LEFT_L = m.ROAM.length + 2 * P.CLR_BAY + CUTOUT[0]   # device plus its cutout

# Right column: bays run along X, cutouts at the +X end.  The column is as
# wide as the longest device plus its cutout.
RIGHT_BAY_W = max(d.length for d in (m.ION, m.TRACKR)) + 2 * P.CLR_BAY + CUTOUT[0]

# Stacked -Y to +Y, per the spec: spare at the bottom, TRACKR, Ion at the top.
_SPARE_L = 46.0   # no device chosen yet (v2.1: was 40)
_TRACKR_L = m.TRACKR.width + 2 * P.CLR_BAY
_ION_L = m.ION.width + 2 * P.CLR_BAY
_RIGHT_L = _SPARE_L + D.THICK + _TRACKR_L + D.THICK + _ION_L   # bays + dividers

# The left bay is stretched to the right column's height; its cutout stays at
# the -Y end, so the ROAM just has more room behind it.
_BAY_L = max(_LEFT_L, _RIGHT_L)

# No frozen numbers on these three: every one of them moves when a
# measurement or a design rule does, and they go stale silently.  The current
# values are in the build report that scripts/export_all.py prints.
TRAY_X = P.V1_WALL + _LEFT_W + RAIL_WALL + RIGHT_BAY_W + RAIL_WALL
TRAY_Y = 2 * P.V1_WALL + _BAY_L
TRAY_H = P.V1_TRAY_PLATE + P.BAY_DEPTH

_Y0 = -TRAY_Y / 2 + P.V1_WALL          # inner face of the -Y wall
_LEFT_X0 = P.V1_WALL
_RIGHT_X0 = _LEFT_X0 + _LEFT_W + RAIL_WALL    # partition's +X face
_RIGHT_X1 = _RIGHT_X0 + RIGHT_BAY_W           # +X outer wall's -X face

ROAM_BAY = (_LEFT_X0, _Y0, _LEFT_W, _BAY_L)

_spare_y = _Y0
_div0_y = _spare_y + _SPARE_L
_trackr_y = _div0_y + D.THICK
_div1_y = _trackr_y + _TRACKR_L
_ion_y = _div1_y + D.THICK

RIGHT_BAYS: dict[str, tuple[float, float, float, float]] = {
    "spare": (_RIGHT_X0, _spare_y, RIGHT_BAY_W, _SPARE_L),
    "trackr": (_RIGHT_X0, _trackr_y, RIGHT_BAY_W, _TRACKR_L),
    # The Ion charges through a socket low in its tail, and MICRO_PLUG is
    # taller than the plate: its overmold does not stand on the plate at all
    # but hangs in the cable cutout, which runs clear through TRAY_PLATE into
    # the base's cable room, so the overmold hangs below the bay floor
    # instead of standing on it.
    "ion": (_RIGHT_X0, _ion_y, RIGHT_BAY_W, _ION_L),
}

# Y centres of the two removable dividers.
RAIL_YS: tuple[float, float] = (_div0_y + D.THICK / 2, _div1_y + D.THICK / 2)

_MIN_XYZ = (Align.MIN, Align.MIN, Align.MIN)
_CTR_MINZ = (Align.CENTER, Align.CENTER, Align.MIN)


def cutout_centres_x(name: str) -> tuple[float, ...]:
    """X centres of the cable cutouts in a right-column bay.

    One cutout inset from the +X end wall by default; bays listed in
    UNDERSIDE_PORT_CUTOUTS get N cutouts evenly spaced along the bay (one
    centred in each of N equal sections)."""
    x0, _, w, _ = RIGHT_BAYS[name]
    n = UNDERSIDE_PORT_CUTOUTS.get(name, 1)
    if n == 1:
        return (x0 + w - CUTOUT_INSET - CUTOUT[0] / 2,)
    section = w / n
    return tuple(x0 + section * (i + 0.5) for i in range(n))


def _cutout(cx: float, cy: float, along: str) -> Part:
    """Through-plate cable cutout centred at (cx, cy); `along` is the bay axis."""
    sx, sy = (CUTOUT[0], CUTOUT[1]) if along == "x" else (CUTOUT[1], CUTOUT[0])
    return Pos(cx, cy, -P.THRU / 2) * Box(sx, sy, P.THRU, align=_CTR_MINZ)


def build_tray() -> Part:
    """The tray, plate-down on the bed: X 0..TRAY_X, Y centred, Z 0..TRAY_H."""
    part = Box(TRAY_X, TRAY_Y, TRAY_H, align=(Align.MIN, Align.CENTER, Align.MIN))
    part = fillet(part.edges().filter_by(Axis.Z), OUTER_R)
    # Downward outer edge of the plate: chamfer, never a fillet.
    part = chamfer(part.faces().sort_by(Axis.Z)[0].edges(), P.CHAMFER)

    # Bay voids, full BAY_DEPTH, open to the top.  The right column is one
    # continuous void: the three bays are only separated when a divider is in.
    # The ROAM bay's two -X corners sit behind the tray's own rounded outer
    # corners, so they are rounded to match; the right column's +X corners
    # stand behind the thicker RAIL_WALL and need no such relief.
    over = 10.0   # run the cutters past the top face for a clean cut
    for x0, y0, w, l, round_min_x in ((_LEFT_X0, _Y0, _LEFT_W, _BAY_L, True),
                                      (_RIGHT_X0, _Y0, RIGHT_BAY_W, _BAY_L, False)):
        void = Box(w, l, P.BAY_DEPTH + over, align=_MIN_XYZ)
        if round_min_x:
            void = fillet(void.edges().filter_by(Axis.Z).group_by(Axis.X)[0],
                          BAY_CORNER_R)
        part -= Pos(x0, y0, P.V1_TRAY_PLATE) * void

    # Rail slots: partition's +X face and the +X outer wall's -X face.
    slot = D.rail_cutter(P.BAY_DEPTH + over)
    slot_dx = (D.RAIL_D + P.CLR_RAIL) / 2
    for y in RAIL_YS:
        part -= Pos(_RIGHT_X0 - slot_dx, y, P.V1_TRAY_PLATE) * slot
        part -= Pos(_RIGHT_X1 + slot_dx, y, P.V1_TRAY_PLATE) * slot

    # Cable cutouts through the plate, inset from each bay's end wall.  They
    # sit well inside the bay footprint, so they never touch a wall.
    part -= _cutout(_LEFT_X0 + _LEFT_W / 2,
                    _Y0 + CUTOUT_INSET + CUTOUT[0] / 2, "y")
    for name, (x0, y0, w, l) in RIGHT_BAYS.items():
        for cx in cutout_centres_x(name):
            part -= _cutout(cx, y0 + l / 2, "x")
    return part
