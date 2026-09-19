"""Base tray: hides the Anker PowerPort 6 and the cable slack; the deck plate
drops into a top rebate and sits flush with the base rim.

The base has its own origin: the box spans X = 0..BASE_X, is centred on Y, and
its underside is the build-plate face at Z = 0.  The deck has its own origin
too, and the two do NOT coincide -- the rebate is inset from the base rim, so
the deck must be moved by `deck_seat()` to sit in it.  Both parts print
underside-down on their own origins; `deck_seat()` is for assembly views and
fit checks only.

Charger orientation: the PowerPort 6 lies flat with its long, six-port face
running along Y.  The ports look toward +X and the C7 mains inlet looks toward
-X, so the pocket is `port_to_inlet` deep in X and `port_face_width` long in Y.
The mains cord therefore leaves through the -X end wall and the status LED
shows through the +X end wall; the device cables leave through the rear (-Y)
escape port.  The charger is pushed to the +X end of the cavity (only
`PORT_PLUG_ROOM_MIN` clear of the port-side wall) so the LED window is close
enough to the LED to carry its light; the leftover length goes to the inlet
side, where the cord just lies on the floor.

It prints open-top-up, so the only ceilings are the escape port, the LED
window and the four foot recesses -- all short bridges.
"""
from build123d import Align, Box, Cylinder, Location, Part, Pos

from dock import deck
from dock import measurements as M
from dock import params as P

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
# rear-wall cutters: centred in X, starting at their given Y and Z
_REAR = (Align.CENTER, Align.MIN, Align.MIN)
# -X end-wall cutters: starting at their given X, centred in Y, up from Z
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)
# +X end-wall cutters: ending at their given X, centred in Y and Z
_END_HI = (Align.MAX, Align.CENTER, Align.CENTER)

CABLE_ROOM = 20.0   # ~10 mm of plug below the plate plus >=8 mm of cable bend
FENCE_H = 8.0       # charger fence height above the floor
CORD_W = 10.0       # AC cord notch width
ESCAPE_H = 12.0     # escape port height
LED_W = 4.0         # LED window side
FOOT_RECESS_D = 0.6  # leaves 1.0 mm of floor under each foot
INLET_PLUG_ROOM = 45.0  # required free X ahead of the inlet for the C7 cord end
PORT_PLUG_ROOM_MIN = 40.0  # required free X in front of the six USB ports

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
# X runs inlet face -> port face; Y runs along the long, six-port face.
POCKET_X = M.CHARGER.port_to_inlet + 2 * P.CLR_FIT
POCKET_Y = M.CHARGER.port_face_width + 2 * P.CLR_FIT
# The fence is placed from the +X (port) side, not the -X (inlet) side: the
# status LED is on the port face and shows through the +X end wall, so the
# charger has to sit as close to that wall as the USB plugs allow.  The cavity
# is much longer than the charger needs, and the slack all lands on the inlet
# side, where a cord lying along the floor does not care.
FENCE_CX = CAVITY_MAX_X - PORT_PLUG_ROOM_MIN - POCKET_X / 2
POCKET_MIN_X = FENCE_CX - POCKET_X / 2   # the inlet face of the charger
POCKET_MAX_X = FENCE_CX + POCKET_X / 2   # the port face of the charger
POCKET_MIN_Y = -POCKET_Y / 2
# Clearance left over inside the cavity, for the build report.
FENCE_MARGIN_X = CAVITY_X - (POCKET_X + 2 * P.WALL)
FENCE_MARGIN_Y = CAVITY_Y - (POCKET_Y + 2 * P.WALL)
PORT_PLUG_ROOM = CAVITY_MAX_X - POCKET_MAX_X   # == PORT_PLUG_ROOM_MIN
INLET_ROOM = POCKET_MIN_X - CAVITY_MIN_X       # whatever is left over

# The ports are numbered from the -Y end of the port face, so the first port
# centre sits at POCKET_MIN_Y + port_face_margin.  On the PowerPort 6 the LED
# is at the *end* of the port row, outboard of port 1 -- away from the other
# five -- so the offset is subtracted, toward -Y.
LED_Y = POCKET_MIN_Y + M.CHARGER.port_face_margin - M.CHARGER.led_offset_from_ports

# Wall cutters span the 2*WALL wall plus a sliver either side, no more.
_WALL_CUT_D = 2 * P.WALL + 0.5
_REAR_CUT_Y0 = -BASE_Y / 2 - 0.25
_END_CUT_X0 = -0.25              # -X end wall: start just outside the face
_END_CUT_X1 = BASE_X + 0.25      # +X end wall: end just outside the face


def deck_seat() -> Location:
    """Where `deck.build_deck()` goes to seat in the rebate."""
    return Pos(P.WALL + P.CLR_FIT, 0, BASE_H - REBATE_D)


def _fence() -> Part:
    """Raised fence that locates the charger, port face toward +X."""
    fence = Box(POCKET_X + 2 * P.WALL, POCKET_Y + 2 * P.WALL, FENCE_H + P.FLOOR,
                align=_MIN)
    fence -= Pos(0, 0, P.FLOOR) * Box(POCKET_X, POCKET_Y, FENCE_H, align=_MIN)
    # fingernail notch through the +Y fence wall, to lift the charger out
    fence -= Pos(0, POCKET_Y / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2, FENCE_H,
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

    # -X end wall: AC cord notch, facing the C7 inlet.  Open to the top so the
    # moulded cord end drops in, down to the inlet centre height, centred on
    # the inlet in Y (the charger is centred on y = 0).
    body -= Pos(_END_CUT_X0, 0, P.FLOOR + M.CHARGER.inlet_center_z) * Box(
        _WALL_CUT_D, CORD_W, BASE_H, align=_END_LO)

    # +X end wall: LED window, square, centred on the LED in Y and on the
    # charger's mid-height in Z.
    body -= Pos(_END_CUT_X1, LED_Y, P.FLOOR + M.CHARGER.height / 2) * Box(
        _WALL_CUT_D, LED_W, LED_W, align=_END_HI)

    # Rear (-Y) wall: cable escape port, one wall below the rebate so the
    # ledge stays continuous.  The cutter starts 0.25 outside the rear face
    # and is 2*WALL + 0.5 deep, so it passes right through the wall and no
    # further.
    body -= Pos(X - 30, _REAR_CUT_Y0, BASE_H - REBATE_D - P.WALL - ESCAPE_H) * Box(
        P.USB_A_PLUG.width + 4, _WALL_CUT_D, ESCAPE_H, align=_REAR)

    # foot recesses
    for fx in (12, X - 12):
        for fy in (-Y / 2 + 12, Y / 2 - 12):
            body -= Pos(fx, fy, 0) * Cylinder(5, FOOT_RECESS_D, align=_MIN)
    return body
