"""Base: the tapered lower shell.  It hides the charger and the cable slack,
carries the tray on a ledge, and the lid on its rim and hinge pins.

The outer faces lean at the draft from the rim (layout.RIM, CORNER_R) down
to the foot, one WALL thick square to the slope, so the corners run from
R30 at the rim to about R8 at the bed.  A V groove at BAND_H is where the
colour changes: dark foot band below, light body above, one tool change
anywhere inside the groove.  Its upper flank is the steeper one, so it
prints.

The tray rests on a ledge ring LEDGE_W proud of the inner wall at the
tray's underside; the ledge's underside leans in, so it prints unsupported.
The tray sits TRAY_SINK below the rim, so the lid lands on the base.

The charger is the v1 arrangement: backed onto the -X end wall in a U
fence, its AC inlet reached from outside through the cord port, an oval
like every other cable hole.  The fence is square-cornered; its arms run
into the leaning end wall and fuse with it, its top is the colour line (so
the whole fence prints dark), and the pocket floor is filleted along the two
side walls to follow the charger's rounded bottom edges.  Two oval escape ports flank the charger in the same wall,
on its flat between the fence and the corner arcs, above the colour groove.

It prints open-top-up with no supports.  Everything that faces down is a
bridge of 20 mm or less -- the ports' flat heads, the foot recesses -- except
the hinge pins' flats, which span the wide hook gap (LONG_BRIDGES).

Base coordinates: XY centred, bed at Z = 0.
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Location, Part, Plane, Pos,
                       SlotCenterToCenter, extrude, fillet, loft)

from dock import hinge as H
from dock import layout as L
from dock import measurements as M
from dock import params as P
from dock import taper

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)

WALL_H = taper.horiz(P.WALL)          # the sloped wall, measured horizontally
BASE_H = L.BASE_H
RIM = L.RIM

# --- tray ledge -----------------------------------------------------------------
LEDGE_W = 3.0
LEDGE_Z = L.TRAY_Z0                   # its top face: the tray's underside lands here

# --- colour groove ----------------------------------------------------------------
GROOVE_D = 0.6                        # depth at BAND_H
GROOVE_LOW = 0.3                      # lower flank height (faces up)
GROOVE_UP = 0.9                       # upper flank height: tall enough to print
GROOVE_H = GROOVE_LOW + GROOVE_UP

# --- charger fence ------------------------------------------------------------------
FENCE_H = P.BAND_H - P.FLOOR          # fence top = the colour line: the whole fence prints dark
POCKET_BACK_SLACK = 2.0               # free X behind the charger, at floor level
PORT_PLUG_ROOM_MIN = 40.0             # least free X in front of the ports
POCKET_X = M.CHARGER.port_to_inlet + 2 * P.CLR_FIT
POCKET_Y = M.CHARGER.port_face_width + 2 * P.CLR_FIT
# The charger's long bottom edges are rounded, so the pocket's floor meets its
# two side walls in a fillet that follows them (not the front wall, and no
# rounded vertical corners anywhere).  Kept below the fence top.
POCKET_FILLET_R = min(M.CHARGER.edge_r + P.CLR_FIT, FENCE_H - 0.5)
FENCE_Y = POCKET_Y + 2 * P.WALL
CAVITY_FLOOR = RIM.at(P.FLOOR, WALL_H)        # (sx, sy, r) of the cavity at the floor
CAVITY_MIN_X, CAVITY_MAX_X = -CAVITY_FLOOR[0] / 2, CAVITY_FLOOR[0] / 2
POCKET_MIN_X = CAVITY_MIN_X + POCKET_BACK_SLACK
POCKET_MAX_X = POCKET_MIN_X + POCKET_X        # the charger's port face
FENCE_MAX_X = POCKET_MAX_X + P.WALL
PORT_PLUG_ROOM = CAVITY_MAX_X - POCKET_MAX_X
FENCE_MARGIN_Y = (CAVITY_FLOOR[1] - FENCE_Y) / 2

# --- cord port (as v1) --------------------------------------------------------------
CORD_W = M.CORD_END.width + 2.0
CORD_H = M.CORD_END.height + 2.0
# The sill must clear the colour groove by at least 0.5 mm; the NOMINAL
# inlet height puts it comfortably above that today, but nothing enforced
# it before, and the groove floor is the higher constraint here.
CORD_Z0 = max(P.FLOOR + M.CHARGER.inlet_center_z - CORD_H / 2,
              P.BAND_H + GROOVE_UP + 0.5)
# Downward faces longer than a 20 mm bridge, printed as bridges anyway: the
# hinge pins' flats span the wide hook gap between the cheeks.
LONG_BRIDGES = ("hinge pins",)

# --- escape ports --------------------------------------------------------------------
ESCAPE_H = 8.0                         # along Z; the ends are full rounds
ESCAPE_Z0 = P.BAND_H + GROOVE_UP + 1.5
ESCAPE_ZC = ESCAPE_Z0 + ESCAPE_H / 2
_ESC = RIM.at(ESCAPE_ZC)
ESCAPE_FLAT_Y = _ESC[1] / 2 - _ESC[2]  # where the -X wall's flat meets its corner arc
# Derived so a full WALL of material remains to the corner arc (and to the
# fence) at this height; 14 is a cap, not a target -- a bigger gap does not
# widen the port past what looks right.
ESCAPE_L = min(14.0, (ESCAPE_FLAT_Y - FENCE_Y / 2) - 2 * P.WALL)
assert ESCAPE_L >= ESCAPE_H, f"escape port too narrow to stay a stadium: {ESCAPE_L:.2f} < {ESCAPE_H}"
ESCAPE_Y = (FENCE_Y / 2 + ESCAPE_FLAT_Y) / 2

# --- floor ---------------------------------------------------------------------------
TIE_D = 4.0
TIE_PITCH = 24.0
TIE_MARGIN = 6.0
FOOT_R = 5.0
FOOT_RECESS_D = 0.6
FOOT_INSET = 12.0
BED_FACE = RIM.at(0.0, taper.bed_chamfer_inset())
FOOT_CENTRES = [(sx * (BED_FACE[0] / 2 - FOOT_INSET), sy * (BED_FACE[1] / 2 - FOOT_INSET))
                for sx in (-1, 1) for sy in (-1, 1)]
_OUTSIDE_X = -RIM.sx / 2 - 5.0         # -X wall cutters start out here


def _grid_axis(lo: float, hi: float, pitch: float) -> list[float]:
    n = int((hi - lo) // pitch)
    start = (lo + hi - n * pitch) / 2
    return [start + i * pitch for i in range(n + 1)]


def _inside_rounded(x, y, sx, sy, r, margin) -> bool:
    hx, hy, rr = sx / 2 - margin, sy / 2 - margin, max(r - margin, 0.0)
    if abs(x) > hx or abs(y) > hy:
        return False
    dx, dy = abs(x) - (hx - rr), abs(y) - (hy - rr)
    return not (dx > 0 and dy > 0) or math.hypot(dx, dy) <= rr


def _tie_grid() -> list[tuple[float, float]]:
    """Tie-down holes on the free floor in front of the fence, clear of the
    walls and the foot recesses."""
    sx, sy, r = CAVITY_FLOOR
    margin = TIE_MARGIN + TIE_D / 2
    xs = _grid_axis(FENCE_MAX_X + margin, CAVITY_MAX_X - margin, TIE_PITCH)
    ys = _grid_axis(-sy / 2 + margin, sy / 2 - margin, TIE_PITCH)
    return [(x, y) for x in xs for y in ys
            if _inside_rounded(x, y, sx, sy, r, margin)
            and all(math.hypot(x - fx, y - fy) > FOOT_R + TIE_D / 2 + 1.0
                    for fx, fy in FOOT_CENTRES)]


TIE_HOLES = _tie_grid()


def tray_seat() -> Location:
    """Moves the tray (its own coordinates) onto the ledge."""
    return Pos(0, 0, L.TRAY_Z0)


def _outer() -> Part:
    foot = loft([RIM.section(0.0, taper.bed_chamfer_inset()), RIM.section(P.CHAMFER)])
    return foot + RIM.solid(P.CHAMFER, BASE_H)


def _ledge() -> Part:
    z0 = LEDGE_Z - LEDGE_W
    band = RIM.solid(z0, LEDGE_Z, inset=WALL_H - 0.05)       # a hair into the wall
    opening = loft([RIM.section(z0 - 0.01, WALL_H - 0.1),
                    RIM.section(LEDGE_Z + 0.01, WALL_H + LEDGE_W)])
    return band - opening


def _fence() -> Part:
    """The U: side arms that run on into the leaning -X wall -- trimmed to the
    base's outside, so they fuse with it along the angle at every height --
    and a front wall.  The pocket is open toward -X, where the end wall
    closes it, and its floor is filleted along the two side walls only."""
    fence = Pos(_OUTSIDE_X, 0, 0) * Box(FENCE_MAX_X - _OUTSIDE_X, FENCE_Y,
                                        P.FLOOR + FENCE_H, align=_END_LO)
    pocket = Pos(_OUTSIDE_X - 1.0, 0, P.FLOOR) * Box(
        POCKET_MAX_X - _OUTSIDE_X + 1.0, POCKET_Y, FENCE_H + 1.0, align=_END_LO)
    pocket = fillet(pocket.edges().filter_by(Axis.X).group_by(Axis.Z)[0], POCKET_FILLET_R)
    return (fence - pocket) & _outer()


def _cord_cutter() -> Part:
    """An oval, like the escape ports: a figure-8 cord end's two lobes fit
    its round ends, and its flat top is short enough to bridge."""
    slot = Plane.YZ.offset(_OUTSIDE_X) * Pos(0, CORD_Z0 + CORD_H / 2) * \
        SlotCenterToCenter(CORD_W - CORD_H, CORD_H)
    return extrude(slot, amount=CAVITY_MIN_X + 1.0 - _OUTSIDE_X)


def _escape_cutters() -> Part:
    cut = None
    for s in (-1, 1):
        slot = Plane.YZ.offset(_OUTSIDE_X) * Pos(s * ESCAPE_Y, ESCAPE_ZC) * \
            SlotCenterToCenter(ESCAPE_L - ESCAPE_H, ESCAPE_H)
        c = extrude(slot, amount=CAVITY_MIN_X + 1.0 - _OUTSIDE_X)
        cut = c if cut is None else cut + c
    return cut


def _groove_cutter() -> Part:
    z0, z1 = P.BAND_H - GROOVE_LOW, P.BAND_H + GROOVE_UP
    core = loft([RIM.section(z0), RIM.section(P.BAND_H, GROOVE_D), RIM.section(z1)],
                ruled=True)
    return RIM.solid(z0, z1, inset=-2.0) - core


def _floor_cutters() -> Part:
    cut = None
    for x, y in TIE_HOLES:
        c = Pos(x, y, -1.0) * Cylinder(TIE_D / 2, P.FLOOR + 2.0, align=_MIN)
        cut = c if cut is None else cut + c
    for x, y in FOOT_CENTRES:
        cut += Pos(x, y, 0) * Cylinder(FOOT_R, FOOT_RECESS_D, align=_MIN)
    return cut


def build_base() -> Part:
    part = _outer() - RIM.solid(P.FLOOR, BASE_H + 1.0, inset=WALL_H)
    part += _ledge()
    part += _fence()
    part -= _cord_cutter()
    part -= _escape_cutters()
    part -= _groove_cutter()
    part -= _floor_cutters()
    part -= H.base_relief()
    part += H.base_knuckles()
    return part
