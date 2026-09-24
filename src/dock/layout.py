"""Where everything goes, as numbers: the tray's four bays, the outlines of
the tray, the base rim and the lid lip, and the heights they stack to.  No
solids here -- tray.py, base.py, lid.py and hinge.py build from these, and
the tests read them to know where to probe.

Coordinates: X and Y are shared by every part and centred on the dock.  Z is
each part's own: the tray's starts at its plate underside, the base's (and
the closed lid's, which is modelled sitting on the base) at the bed.

The bays are sized at the tray floor, and everything grows from there: the
tray's outer walls lean out at the draft from the floor up to its rim, the
base rim wraps that with TRAY_GAP and a WALL, and the lid continues the
slope above the rim.  Bay sides on the tray's outer wall are "sloped": a
device needs only CLR_BAY_OUTER there at the floor, because the lean opens
the gap to about 13 mm by the rim, which is where a cable runs.  Sides on an
internal wall stand vertical and keep v1's CLR_BAY.
"""
from dataclasses import dataclass

from dock import measurements as m
from dock import params as P
from dock import taper

CABLE_ROOM = 6.0          # headroom over the charger, under the tray
CUTOUT = (28.0, 16.0)     # cable cutout: (along the bay, across it), as v1
CUTOUT_INSET = 3.5        # cutout to the bay's end, clear of the R3 floor fillet
CUTOUT_GAP = 6.0          # cutout to the device, as v1
SPARE_L = 46.0            # the spare bay: no device chosen yet
INNER_FILLET_R = 6.0      # vertical inside corners of the bays
FLOOR_FILLET_R = 3.0      # where every bay wall meets the floor
# The tray's outer wall runs this far (horizontally) clear of the base's
# inner wall, more than a fit clearance, so the ledge sets the tray's height
# rather than the two tapers wedging together.
TRAY_GAP = P.CLR_FIT + 0.3
TRAY_SINK = 0.3           # tray rim below the base rim: the lid lands on the base
LID_SLOPE_H = 5.0         # the lid's lower band, continuing the base's slope
LIP_H = 3.0               # its flared top band
LID_H = LID_SLOPE_H + LIP_H
LIP_W_MAX = 2.0           # how far the lip stands proud of the slope, bed allowing
BED_MARGIN = 0.25         # the lid is the widest part; keep it this far inside the bed


@dataclass(frozen=True)
class Bay:
    """A bay's floor rectangle, tray coordinates, and which of its sides
    (-X, +X, -Y, +Y) lie on the tray's sloped outer wall."""
    name: str
    x0: float
    x1: float
    y0: float
    y1: float
    sloped: tuple[bool, bool, bool, bool]

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.y0 + self.y1) / 2


# Left bay: the ROAM, long axis along Y, its cutout at the -Y end.  Right
# column, stacked -Y to +Y: spare, TRACKR, Ion, long axes along X, lying
# against the partition with their cutouts at the +X end.
_LEFT_W = m.ROAM.width + P.CLR_BAY_OUTER + P.CLR_BAY
_LEFT_L = CUTOUT_INSET + CUTOUT[0] + CUTOUT_GAP + m.ROAM.length + P.CLR_BAY_OUTER
_RIGHT_W = (max(d.length for d in (m.ION, m.TRACKR))
            + P.CLR_BAY + CUTOUT_GAP + CUTOUT[0] + CUTOUT_INSET)
_TRACKR_L = m.TRACKR.width + 2 * P.CLR_BAY
_ION_L = m.ION.width + P.CLR_BAY + P.CLR_BAY_OUTER
_RIGHT_L = SPARE_L + P.WALL + _TRACKR_L + P.WALL + _ION_L
BAY_L = max(_LEFT_L, _RIGHT_L)          # the shorter column is stretched to match
FLOOR_X = _LEFT_W + P.WALL + _RIGHT_W   # the bays and the partition, at the floor
FLOOR_Y = BAY_L

_X0, _Y0 = -FLOOR_X / 2, -FLOOR_Y / 2
_XR = _X0 + _LEFT_W + P.WALL
_Y_TRACKR = _Y0 + SPARE_L + P.WALL
_Y_ION = _Y_TRACKR + _TRACKR_L + P.WALL
BAYS: dict[str, Bay] = {
    "roam": Bay("roam", _X0, _X0 + _LEFT_W, _Y0, -_Y0, (True, False, True, True)),
    "spare": Bay("spare", _XR, -_X0, _Y0, _Y0 + SPARE_L, (False, True, True, False)),
    "trackr": Bay("trackr", _XR, -_X0, _Y_TRACKR, _Y_TRACKR + _TRACKR_L,
                  (False, True, False, False)),
    "ion": Bay("ion", _XR, -_X0, _Y_ION, -_Y0, (False, True, False, True)),
}

# --- heights ------------------------------------------------------------------
TRAY_H = P.TRAY_PLATE + P.BAY_DEPTH
BASE_H = P.FLOOR + m.CHARGER.height + CABLE_ROOM + TRAY_SINK + TRAY_H
TRAY_Z0 = BASE_H - TRAY_SINK - TRAY_H   # the tray's underside, base coordinates

# --- outlines -----------------------------------------------------------------
_TRAY_WALL_H = taper.horiz(P.THIN_WALL)
_BASE_WALL_H = taper.horiz(P.WALL)
_TRAY_GROW = _TRAY_WALL_H + P.BAY_DEPTH * taper.TAN      # floor -> tray rim
_RIM_GROW = TRAY_GAP + _BASE_WALL_H + TRAY_SINK * taper.TAN  # tray rim -> base rim
# The tray's outer face at its rim (tray coordinates), and the base's at its
# rim.  One corner centre serves both, so the gap is uniform through the
# corners; CORNER_R is the base rim's.
TRAY_OUTLINE = taper.Outline(FLOOR_X + 2 * _TRAY_GROW, FLOOR_Y + 2 * _TRAY_GROW,
                             P.CORNER_R - _RIM_GROW, z_ref=TRAY_H)
RIM = taper.Outline(TRAY_OUTLINE.sx + 2 * _RIM_GROW, TRAY_OUTLINE.sy + 2 * _RIM_GROW,
                    P.CORNER_R, z_ref=BASE_H)
# The lid is the widest part: the lip gives way to the bed if it has to.
_SLOPE_TOP = RIM.at(BASE_H + LID_SLOPE_H)
LIP_W = min(LIP_W_MAX,
            (P.BED_X - _SLOPE_TOP[0]) / 2 - BED_MARGIN,
            (P.BED_Y - _SLOPE_TOP[1]) / 2 - BED_MARGIN)

# --- what lies in the bays ------------------------------------------------------
DEVICES = {"roam": m.ROAM, "trackr": m.TRACKR, "ion": m.ION}


def device_footprint(name: str) -> tuple[float, float, float, float]:
    """(x0, x1, y0, y1) of a device lying in its bay, tray coordinates."""
    b = BAYS[name]
    d = DEVICES[name]
    if name == "roam":   # just past its cutout at the -Y end
        x0 = b.x0 + P.CLR_BAY_OUTER
        y0 = b.y0 + CUTOUT_INSET + CUTOUT[0] + CUTOUT_GAP
        return x0, x0 + d.width, y0, y0 + d.length
    x0 = b.x0 + P.CLR_BAY          # against the partition
    y0 = b.y0 + P.CLR_BAY
    return x0, x0 + d.length, y0, y0 + d.width


def cutouts() -> list[tuple[str, float, float, float, float]]:
    """(bay, cx, cy, sx, sy) of every cable cutout, tray coordinates: one
    per bay, at its outer end."""
    b = BAYS["roam"]
    out = [("roam", b.cx, b.y0 + CUTOUT_INSET + CUTOUT[0] / 2, CUTOUT[1], CUTOUT[0])]
    for name in ("spare", "trackr", "ion"):
        b = BAYS[name]
        out.append((name, b.x1 - CUTOUT_INSET - CUTOUT[0] / 2, b.cy, CUTOUT[0], CUTOUT[1]))
    return out
