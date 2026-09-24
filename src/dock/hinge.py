"""Snap-on lid hinge: the base carries the pins, the lid the hooks.

Everything here is in base coordinates, with the lid modelled closed on the
rim; lid.py turns the lid over for printing.  The axis runs along X at rim
height, AXIS_Y behind the +Y rim -- far enough that nothing near it sweeps
into the tray.  Two stations stand HINGE_INSET in from each end.

At each station the base carries two cheeks with a pin between them.  A
cheek is a disc round the axis hulled with a 45 degree chin that runs down
into the wall, so it prints open-top-up without supports; the pin's
underside is cut flat at PIN_FLAT*PIN_R -- a flat 3 mm wide, bridged between
the cheeks (base.LONG_BRIDGES) -- which keeps it inside the bore circle.

The lid carries a hook between the cheeks: a ring round the pin with a plain
round bore, hulled into the lid's back wall and top.  Its mouth faces
straight down with the lid closed (MOUTH_DEG): a neck SNAP narrower than the
pin, then a flare.  The lid presses straight down onto the pins and pulls
straight up off them, with a light snap either way.  As printed (top face
down) the mouths face up, so the bores print on supports.

A heel tab at X = 0 stops the lid at OPEN_DEG: its tip lands on the base's
outer wall there.  OPEN_DEG is kept short of 110 on purpose: resting on the
heel, the lid pushes its hooks toward the front, which is close to the
mouths' direction once the lid is open, and the further it leans back the
harder that push.

Each part's knuckles turn inside relief discs (RELIEF_R round the axis) cut
out of the other part.  A disc round the axis is the same at every angle, so
the swing clears however far the lid turns.
"""
import math

from build123d import Align, Box, Cylinder, Location, Part, Plane, Polygon, Pos, Rot, extrude

from dock import layout as L
from dock import params as P
from dock import taper

PIN_R = 2.5
PIN_FLAT = 0.8            # pin underside cut flat this far (x PIN_R) below the axis
BORE_CLR = 0.4            # tune on the hinge coupon
BORE_R = PIN_R + BORE_CLR
SNAP = 0.2                # neck narrower than the pin by this: a light snap; tune on the coupon
MOUTH_W = 2 * PIN_R - SNAP
THROAT = 1.0              # neck length past the bore before the mouth flares
KNUCKLE_R = 5.5
RELIEF_R = KNUCKLE_R + 0.5
HOOK_W = 24.0
CHEEK_W = 12.0
SIDE_CLR = 0.3            # hook to cheek, along X
HINGE_INSET = 60.0        # station centre in from each end of the rim
OPEN_DEG = 100.0
MOUTH_DEG = -90.0          # closed-lid mouth angle, from +Y toward +Z: straight down
HEEL_R = 7.0              # heel tip centre, from the axis
HEEL_TIP_R = 1.0
HEEL_W = 24.0
AXIS_GAP = 0.2            # knuckle sweep to tray, at the rim

AXIS_Y = L.TRAY_OUTLINE.sy / 2 + RELIEF_R + AXIS_GAP
AXIS_Z = L.BASE_H
STATIONS = (-(L.RIM.sx / 2 - HINGE_INSET), L.RIM.sx / 2 - HINGE_INSET)

_RIM_Y = L.RIM.sy / 2
_BASE_WALL_H = taper.horiz(P.WALL)
_LID_WALL_Y = _RIM_Y - 0.3          # inside the lid's back wall at every height of it
_LID_TOP = L.BASE_H + L.LID_H
_ALONG = (Align.CENTER, Align.CENTER, Align.MIN)


def hull2d(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Convex hull, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted(set((round(a, 9), round(b, 9)) for a, b in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    upper: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _circle(cy: float, cz: float, r: float, n: int = 48) -> list[tuple[float, float]]:
    return [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def _polar(r: float, deg: float) -> tuple[float, float]:
    """(Y, Z) of the point `r` from the axis at `deg` above +Y."""
    a = math.radians(deg)
    return AXIS_Y + r * math.cos(a), AXIS_Z + r * math.sin(a)


def _prism(points_yz, x0: float, x1: float) -> Part:
    """A YZ polygon extruded along X from x0 to x1."""
    return extrude(Plane.YZ.offset(x0) * Polygon(*points_yz, align=None), amount=x1 - x0)


def x_cylinder(r: float, x0: float, x1: float) -> Part:
    """A cylinder of radius r round the hinge axis, from x0 to x1."""
    return Pos(x0, AXIS_Y, AXIS_Z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0, align=_ALONG)


def opened(deg: float = 0.0) -> Location:
    """Turns a closed lid, in base coordinates, `deg` open about the axis."""
    return Pos(0, AXIS_Y, AXIS_Z) * Rot(-deg, 0, 0) * Pos(0, -AXIS_Y, -AXIS_Z)


def wall_gap(y: float, z: float) -> float:
    """Signed distance from (y, z) to the base's +Y outer face, outside > 0."""
    return ((y - _RIM_Y) + (L.BASE_H - z) * taper.TAN) * taper.COS


def _heel_closed_deg() -> float:
    """Where the heel tip points with the lid closed: the angle that puts it
    HEEL_TIP_R off the outer wall when the lid is at OPEN_DEG."""
    lo, hi = -175.0, -95.0      # wall_gap at hi is > HEEL_TIP_R, at lo < it
    g_lo, g_hi = wall_gap(*_polar(HEEL_R, lo)), wall_gap(*_polar(HEEL_R, hi))
    assert g_hi > HEEL_TIP_R > g_lo, (
        f"heel bisection bracket [{lo}, {hi}] does not bracket the root: "
        f"wall_gap(lo)={g_lo:.3f}, wall_gap(hi)={g_hi:.3f}, target={HEEL_TIP_R}")
    for _ in range(60):
        mid = (lo + hi) / 2
        if wall_gap(*_polar(HEEL_R, mid)) > HEEL_TIP_R:
            hi = mid
        else:
            lo = mid
    return hi + OPEN_DEG


HEEL_DEG = _heel_closed_deg()


def _gap_ends(xs: float) -> tuple[float, float]:
    """X of the two cheek faces either side of the hook at station xs."""
    return xs - HOOK_W / 2 - SIDE_CLR, xs + HOOK_W / 2 + SIDE_CLR


def _cheek_profile() -> list[tuple[float, float]]:
    ty, tz = _polar(KNUCKLE_R, -45.0)        # where the 45-degree chin leaves the disc
    mid = _RIM_Y - _BASE_WALL_H / 2          # the wall's mid-surface at the rim
    # run the chin down-and-in at 45 degrees until it meets that mid-surface
    zw = (mid - L.BASE_H * taper.TAN - ty + tz) / (1 - taper.TAN)
    yw = ty - (tz - zw)
    return hull2d(_circle(AXIS_Y, AXIS_Z, KNUCKLE_R) + [(yw, zw), (mid, AXIS_Z)])


def base_knuckles(stations=STATIONS) -> Part:
    """The cheeks and pins, to be added to the base."""
    prof = _cheek_profile()
    part = None
    for xs in stations:
        a, b = _gap_ends(xs)
        flat = Pos(xs, AXIS_Y, AXIS_Z - PIN_FLAT * PIN_R) * Box(
            b - a + 2, 2 * PIN_R + 1, PIN_R, align=(Align.CENTER, Align.CENTER, Align.MAX))
        pin = x_cylinder(PIN_R, a - 0.5, b + 0.5) - flat
        station = _prism(prof, a - CHEEK_W, a) + _prism(prof, b, b + CHEEK_W) + pin
        part = station if part is None else part + station
    return part


def base_relief(stations=STATIONS) -> Part:
    """What the base gives up so the hooks can turn."""
    part = None
    for xs in stations:
        c = x_cylinder(RELIEF_R, *_gap_ends(xs))
        part = c if part is None else part + c
    return part


def lid_relief(stations=STATIONS) -> Part:
    """What the lid gives up so it can turn round the cheeks."""
    part = None
    for xs in stations:
        a, b = _gap_ends(xs)
        for c in (x_cylinder(RELIEF_R, a - CHEEK_W - SIDE_CLR, a + SIDE_CLR),
                  x_cylinder(RELIEF_R, b - SIDE_CLR, b + CHEEK_W + SIDE_CLR)):
            part = c if part is None else part + c
    return part


def _mouth_profile() -> list[tuple[float, float]]:
    a = math.radians(MOUTH_DEG)
    u = (math.cos(a), math.sin(a))
    n = (-math.sin(a), math.cos(a))
    r1, r2 = BORE_R + THROAT, KNUCKLE_R + 3.0
    w1, w2 = MOUTH_W / 2, BORE_R + 0.5
    local = [(0, -w1), (r1, -w1), (r2, -w2), (r2, w2), (r1, w1), (0, w1)]
    return [(AXIS_Y + s * u[0] + t * n[0], AXIS_Z + s * u[1] + t * n[1]) for s, t in local]


def lid_hooks(stations=STATIONS) -> Part:
    """The hooks, closed-lid position, to be added to the lid."""
    k = KNUCKLE_R
    prof = hull2d(_circle(AXIS_Y, AXIS_Z, k) + [
        (_LID_WALL_Y, AXIS_Z), (_LID_WALL_Y, _LID_TOP), (AXIS_Y + k, _LID_TOP)])
    bore = _circle(AXIS_Y, AXIS_Z, BORE_R, 96)
    mouth = _mouth_profile()
    part = None
    for xs in stations:
        x0, x1 = xs - HOOK_W / 2, xs + HOOK_W / 2
        hook = _prism(prof, x0, x1) - _prism(bore, x0 - 1, x1 + 1) - _prism(mouth, x0 - 1, x1 + 1)
        part = hook if part is None else part + hook
    return part


def heel_tab() -> Part:
    """The stop, closed-lid position, to be added to the lid at X = 0."""
    ty, tz = _polar(HEEL_R, HEEL_DEG)
    prof = hull2d(_circle(ty, tz, HEEL_TIP_R, 16) + [
        (ty + HEEL_TIP_R, _LID_TOP), (_LID_WALL_Y, _LID_TOP),
        (_LID_WALL_Y, _LID_TOP - P.LID_PLATE)])
    return _prism(prof, -HEEL_W / 2, HEEL_W / 2)
