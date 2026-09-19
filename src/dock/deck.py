"""Top deck: a solid plate carrying three cradles and a spare bay.

Coordinates: the plate spans X = 0..DECK_X, is centred on Y, and its underside
is the build-plate face at Z = 0.  The whole plate sits on the bed, so the deck
prints cradles-up with no unsupported bridge and no skirt.

The plate is `PLATE_T` thick and every station's floor slot runs through all of
it: that depth of bore is what grips the cable's device-end plug, leaving the
metal tip proud of the cradle floor.  The base receives the plate in a rebate,
so the deck itself carries no lip or inset.
"""
from functools import lru_cache

from build123d import Align, Axis, Box, Part, Pos, Rot

from dock import cradles, divider
from dock import measurements as M
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_THRU = 400.0      # cutter length; longer than anything on the deck

PLATE_T = 8.0      # plate thickness = plug engagement depth
SPARE_W, SPARE_L, SPARE_H = 40.0, 70.0, 30.0   # X, Y, wall height
# The bay's +/-X walls carry the divider rail slots, so they are thick enough
# to leave WALL of material behind each slot.  The +/-Y walls stay WALL.
SPARE_WALL_X = P.WALL + divider.RAIL_D + P.CLR_RAIL
_ORDER = ("ion", "roam", "trackr", "spare")

# Plug captured by each station's floor slot, and the slot's tilt from
# vertical.  Only the Roam's slot is tilted: it runs normal to the tilted
# shelf floor, and stays normal to it through the plate so a rigid plug
# pushes straight in.
_PLUGS: dict[str, tuple[P.Plug, float]] = {
    "ion": (P.MICRO_PLUG, 0.0),
    "roam": (P.USB_C_PLUG, cradles.ROAM_TILT),
    "trackr": (P.USB_C_PLUG, 0.0),
    "spare": (P.USB_A_PLUG, 0.0),
}


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
    bay = Box(SPARE_W + 2 * SPARE_WALL_X, SPARE_L + 2 * P.WALL,
              SPARE_H + P.FLOOR, align=_MIN)
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


# Clearance the base leaves between the charger fence and the lower cavity
# wall, per side.  It is a base concern, but the deck's Y is what drives the
# base's Y, so the floor on DECK_Y has to be computed here (base imports deck,
# not the other way round).
FENCE_GAP_Y = 2.0

# base.CAVITY_Y == BASE_Y - 4*WALL == DECK_Y + 2*(WALL + CLR_FIT) - 4*WALL,
# and the cavity has to swallow the charger pocket plus the fence walls plus
# FENCE_GAP_Y per side:
#     CAVITY_Y >= (port_face_width + 2*CLR_FIT) + 2*WALL + 2*FENCE_GAP_Y
# Solving for DECK_Y:
MIN_DECK_Y = (M.CHARGER.port_face_width + 2 * P.CLR_FIT   # charger pocket (Y)
              + 2 * P.WALL                                # fence walls
              + 2 * FENCE_GAP_Y                           # fence-to-cavity gap
              + 2 * (2 * P.WALL)                          # cavity walls
              - 2 * (P.WALL + P.CLR_FIT))                 # deck -> base offset

DECK_X = P.WALL + sum(s[1] + P.WALL for s in _stations())
# The stations stay centred on y = 0; the plate is widened symmetrically when
# the charger below needs more room than the tallest station does.
DECK_Y = max(max(s[2] for s in _stations()) + 2 * P.WALL, MIN_DECK_Y)
SPARE_BAY = (*layout()["spare"], SPARE_W, SPARE_L, SPARE_H)


def build_deck() -> Part:
    part = Pos(DECK_X / 2, 0, 0) * Box(DECK_X, DECK_Y, PLATE_T, align=_MIN)

    bores = []
    for name, (x, y) in layout().items():
        station = _station(name)
        # sink each station by its own FLOOR so its floor merges into the
        # top of the plate
        part += Pos(x, y, PLATE_T - P.FLOOR) * station

        plug, tilt = _PLUGS[name]
        mx, my = _slot_mouth(station)
        at = Pos(x + mx, y + my, PLATE_T - P.FLOOR) * Rot(tilt, 0, 0)
        bores.append(at * Box(plug.width + 2 * P.CLR_DEVICE,
                              plug.height + 2 * P.CLR_DEVICE,
                              _THRU, align=_CTR))

    # re-cut every slot through the full plate thickness
    for bore in bores:
        part -= bore

    return part
