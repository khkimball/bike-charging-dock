"""Base tray: hides the Anker PowerPort 6 and the cable slack; the deck plate
drops into a top rebate and sits flush with the base rim.

The base has its own origin: the box spans X = 0..BASE_X, is centred on Y, and
its underside is the build-plate face at Z = 0.  The deck has its own origin
too, and the two do NOT coincide -- the rebate is inset from the base rim, so
the deck must be moved by `deck_seat()` to sit in it.  Both parts print
underside-down on their own origins; `deck_seat()` is for assembly views and
fit checks only.

It prints open-top-up, so the only ceilings are the short bridges over the
rear-wall through-holes.
"""
from build123d import Align, Box, Cylinder, Location, Part, Pos

from dock import deck
from dock import measurements as M
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
# rear-wall cutters: centred in X, starting at their given Y and Z
_REAR = (Align.CENTER, Align.MIN, Align.MIN)

CABLE_ROOM = 20.0   # ~10 mm of plug below the plate plus >=8 mm of cable bend
FENCE_H = 8.0       # charger fence height above the floor
CORD_W = 10.0       # AC cord notch width
ESCAPE_H = 12.0     # escape port height
LED_W = 4.0         # LED window side
FOOT_RECESS_D = 0.6  # leaves 1.0 mm of floor under each foot
INLET_PLUG_ROOM = 25.0  # free X ahead of the charger inlet for the C7 cord end

REBATE_D = deck.PLATE_T
BASE_X = deck.DECK_X + 2 * (P.WALL + P.CLR_FIT)
BASE_Y = deck.DECK_Y + 2 * (P.WALL + P.CLR_FIT)
BASE_H = P.FLOOR + M.CHARGER.height + CABLE_ROOM + REBATE_D

# Walls below the rebate are 2*WALL thick, so the rebate leaves a ledge.
CAVITY_X = BASE_X - 4 * P.WALL
CAVITY_Y = BASE_Y - 4 * P.WALL
CAVITY_MIN_X, CAVITY_MAX_X = 2 * P.WALL, BASE_X - 2 * P.WALL
REBATE_X = deck.DECK_X + 2 * P.CLR_FIT
REBATE_Y = deck.DECK_Y + 2 * P.CLR_FIT
LEDGE_W = (REBATE_X - CAVITY_X) / 2          # shelf width (== WALL)
PLATE_BEARING_W = (deck.DECK_X - CAVITY_X) / 2  # width the plate actually lands on

# Charger pocket inside the fence, and the fence footprint around it.
CH_L = M.CHARGER.length + 2 * P.CLR_FIT
CH_W = M.CHARGER.width + 2 * P.CLR_FIT
FENCE_CX = CAVITY_MIN_X + INLET_PLUG_ROOM + CH_L / 2  # room to plug the cord in
POCKET_MIN_X = FENCE_CX - CH_L / 2
POCKET_MAX_X = FENCE_CX + CH_L / 2
# Clearance left over inside the cavity, for the build report.
FENCE_MARGIN_X = CAVITY_X - (CH_L + 2 * P.WALL)
FENCE_MARGIN_Y = CAVITY_Y - (CH_W + 2 * P.WALL)

# Rear cutters span the 2*WALL wall plus a sliver either side, no more.
_REAR_CUT_D = 2 * P.WALL + 0.5
_REAR_CUT_Y0 = -BASE_Y / 2 - 0.25


def deck_seat() -> Location:
    """Where `deck.build_deck()` goes to seat in the rebate."""
    return Pos(P.WALL + P.CLR_FIT, 0, BASE_H - REBATE_D)


def _fence() -> Part:
    """Raised fence that locates the charger, port face toward +X."""
    fence = Box(CH_L + 2 * P.WALL, CH_W + 2 * P.WALL, FENCE_H + P.FLOOR,
                align=_MIN)
    fence -= Pos(0, 0, P.FLOOR) * Box(CH_L, CH_W, FENCE_H, align=_MIN)
    # fingernail notch through the +Y fence wall, to lift the charger out
    fence -= Pos(0, CH_W / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2, FENCE_H,
                                             align=_MIN)
    return fence


def build_base() -> Part:
    X, Y = BASE_X, BASE_Y
    cx = X / 2
    body = Pos(cx, 0, 0) * Box(X, Y, BASE_H, align=_MIN)
    # lower cavity: walls 2*WALL thick so the rebate leaves a ledge
    body -= Pos(cx, 0, P.FLOOR) * Box(CAVITY_X, CAVITY_Y, BASE_H, align=_MIN)
    # rebate that receives the deck plate flush with the top
    body -= Pos(cx, 0, BASE_H - REBATE_D) * Box(REBATE_X, REBATE_Y, REBATE_D,
                                                align=_MIN)

    body += Pos(FENCE_CX, 0, 0) * _fence()

    # Rear (-Y) wall cut-outs.  Each cutter starts 0.25 outside the rear face
    # and is 2*WALL + 0.5 deep, so it passes right through the wall and no
    # further.
    rear_y = _REAR_CUT_Y0
    # AC cord notch: open to the top, down to the inlet centre, in line with
    # the charger's inlet face.  The clamp is a guard that keeps the notch off
    # the -X wall if the fence is ever moved back.
    notch_x = max(FENCE_CX - CH_L / 2, CAVITY_MIN_X + CORD_W / 2)
    body -= Pos(notch_x, rear_y, P.FLOOR + M.CHARGER.inlet_center_z) * Box(
        CORD_W, _REAR_CUT_D, BASE_H, align=_REAR)
    # cable escape port, one wall below the rebate so the ledge stays continuous
    body -= Pos(X - 30, rear_y, BASE_H - REBATE_D - P.WALL - ESCAPE_H) * Box(
        P.USB_A_PLUG.width + 4, _REAR_CUT_D, ESCAPE_H, align=_REAR)
    # LED window
    led_x = (FENCE_CX + CH_L / 2 - M.CHARGER.port_face_margin
             - M.CHARGER.led_offset_from_ports)
    body -= Pos(led_x, rear_y, P.FLOOR + M.CHARGER.height / 2) * Box(
        LED_W, _REAR_CUT_D, LED_W, align=_REAR)

    # foot recesses
    for fx in (12, X - 12):
        for fy in (-Y / 2 + 12, Y / 2 - 12):
            body -= Pos(fx, fy, 0) * Cylinder(5, FOOT_RECESS_D, align=_MIN)
    return body
