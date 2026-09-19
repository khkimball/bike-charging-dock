"""Top deck: plate + lip + three cradles + spare bay with divider slots.

Coordinates: the plate spans X = 0..DECK_X, is centred on Y and its underside
is the build-plate face at Z = 0 of the *construction* frame.  Everything is
lifted by WELL_H at the end so the finished part sits on Z = 0.

Under every floor slot hangs a plug well: a WALL-thick rectangular boss that
grips the cable's device-end plug over its whole overmold length, leaving the
metal tip proud of the cradle floor.  The wells are the deepest thing on the
deck (deeper than the lip), so they, not the lip, set the Z offset.
"""
import math
from functools import lru_cache

from build123d import Align, Axis, Box, Part, Pos, Rot

from dock import cradles, divider
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_MAX = (Align.CENTER, Align.CENTER, Align.MAX)
_THRU = 400.0      # cutter length; longer than anything on the deck

LIP_H = 6.0
SPARE_W, SPARE_L, SPARE_H = 40.0, 70.0, 30.0   # X, Y, wall height
_ORDER = ("ion", "roam", "trackr", "spare")

# Plug captured under each station's floor slot, and the slot's tilt from
# vertical.  Only the Roam's slot is tilted: it runs normal to the tilted
# shelf floor, so its well leans with it and the plug pushes in straight.
_PLUGS: dict[str, tuple[P.Plug, float]] = {
    "ion": (P.MICRO_PLUG, 0.0),
    "roam": (P.USB_C_PLUG, cradles.ROAM_TILT),
    "trackr": (P.USB_C_PLUG, 0.0),
    "spare": (P.USB_A_PLUG, 0.0),
}

# Every well reaches the bed, so they are all as deep as the longest plug;
# a shorter well would leave its pillar hanging in mid-air.  Task 7 sizes the
# base cavity from this.
WELL_H = max(plug.length for plug, _ in _PLUGS.values())


@lru_cache(maxsize=None)
def _station(name: str) -> Part:
    """The station solid, on the bed and centred on its own footprint."""
    return {"ion": cradles.build_ion_cradle,
            "roam": cradles.build_roam_cradle,
            "trackr": cradles.build_trackr_cradle,
            "spare": _spare_bay}[name]()


def _stations() -> list[tuple[str, float, float]]:
    """(name, x_size, y_size) in row order."""
    return [(n, *cradles.cradle_footprint(_station(n))) for n in _ORDER]


def layout() -> dict[str, tuple[float, float]]:
    x = P.WALL
    out = {}
    for name, sx, _ in _stations():
        out[name] = (x + sx / 2, 0.0)
        x += sx + P.WALL
    return out


def _spare_bay() -> Part:
    bay = Box(SPARE_W + 2 * P.WALL, SPARE_L + 2 * P.WALL, SPARE_H + P.FLOOR,
              align=_MIN)
    bay -= Pos(0, 0, P.FLOOR) * Box(SPARE_W, SPARE_L, SPARE_H, align=_MIN)
    bay -= Box(P.USB_A_PLUG.width + 2 * P.CLR_DEVICE,
               P.USB_A_PLUG.height + 2 * P.CLR_DEVICE, _THRU, align=_CTR)
    # two divider positions; the rails cut into both long walls and stay
    # wholly inside them
    x_rail = SPARE_W / 2 + (divider.RAIL_D + P.CLR_RAIL) / 2
    for y in (-SPARE_L / 4, SPARE_L / 4):
        for x in (x_rail, -x_rail):
            bay -= Pos(x, y, P.FLOOR) * divider.rail_cutter(SPARE_H)
    return bay


def _slot_mouth(part: Part) -> tuple[float, float]:
    """XY centre of the station's floor slot, read off its bed face."""
    inner = part.faces().sort_by(Axis.Z)[0].inner_wires()
    if len(inner) != 1:
        raise ValueError(f"expected one floor slot, found {len(inner)}")
    c = inner[0].bounding_box().center()
    return c.X, c.Y


DECK_X = P.WALL + sum(s[1] + P.WALL for s in _stations())
DECK_Y = max(s[2] for s in _stations()) + 2 * P.WALL
SPARE_BAY = (*layout()["spare"], SPARE_W, SPARE_L, SPARE_H)


def build_deck() -> Part:
    cx = DECK_X / 2
    part = Pos(cx, 0, 0) * Box(DECK_X, DECK_Y, P.FLOOR, align=_MIN)

    # lip: a WALL-thick skirt hanging LIP_H below the plate, inset so it
    # drops into the base
    inset = P.WALL + P.CLR_FIT
    outer = Box(DECK_X - 2 * inset, DECK_Y - 2 * inset, LIP_H, align=_MAX)
    inner = Box(DECK_X - 2 * (inset + P.WALL), DECK_Y - 2 * (inset + P.WALL),
                LIP_H + 2, align=_MAX)
    part += Pos(cx, 0, 0) * (outer - inner)

    bores = []
    for name, (x, y) in layout().items():
        station = _station(name)
        # the station carries its own FLOOR, so at Z=0 it merges with the plate
        part += Pos(x, y, 0) * station

        plug, tilt = _PLUGS[name]
        mx, my = _slot_mouth(station)
        at = Pos(x + mx, y + my, 0) * Rot(tilt, 0, 0)
        # overlength so the trim below leaves a full-depth well even when it
        # leans; trimmed flat, the leaning well still supports the plug over
        # WELL_H / cos(tilt) of its travel
        length = (WELL_H + 5.0) / math.cos(math.radians(tilt))
        part += at * Box(plug.width + 2 * P.CLR_DEVICE + 2 * P.WALL,
                         plug.height + 2 * P.CLR_DEVICE + 2 * P.WALL,
                         length, align=_MAX)
        bores.append(at * Box(plug.width + 2 * P.CLR_DEVICE,
                              plug.height + 2 * P.CLR_DEVICE,
                              _THRU, align=_CTR))

    # flatten every well onto one bed plane
    part -= Pos(cx, 0, -WELL_H) * Box(2 * DECK_X, 2 * DECK_Y, _THRU, align=_MAX)
    # re-cut each slot through plate and well in one pass
    for bore in bores:
        part -= bore

    return Pos(0, 0, WELL_H) * part
