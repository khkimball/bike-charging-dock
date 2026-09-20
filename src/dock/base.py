"""Base: the rounded-corner lower box.  It hides the Anker PowerPort 6 and
the cable slack, and the tray drops into a rebate in its top rim.

The base has its own origin: the box spans X = 0..BASE_X, is centred on Y,
and its underside is the build-plate face at Z = 0.  The tray has its own
origin too, and the two do NOT coincide -- the rebate is inset from the base
rim, so the tray must be moved by `tray_seat()` to sit in it.  Both parts
print underside-down on their own origins; `tray_seat()` is for assembly
views and fit checks only.

Charger orientation: the PowerPort 6 lies flat with its long, six-port face
running along Y.  The ports look toward +X and the C7 mains inlet looks
toward -X, so the pocket is `port_to_inlet` deep in X and `port_face_width`
long in Y.  The mains cord leaves through a closed port in the -X end wall,
the status LED shows through the +X end wall, and the device cables leave
through the rear (-Y) escape port under the tray's spare bay.

Wall stack-up, bottom to top: the shell below the rebate is 2*WALL thick so
the rebate can be cut back to the tray's own footprint and still leave a
continuous ledge all round; above the ledge the rim is WALL thick.  The outer
vertical corners are CORNER_R, the cavity corners CORNER_R - 2*WALL, and the
rebate corners the tray's OUTER_R + CLR_FIT -- all three arcs share a centre,
so the ledge is a band of uniform width.  The bottom outer edge is chamfered,
never filleted: it is a downward edge.

BASE_Y grows if a remeasured charger needs a wider fence (the rebate stays
tray-sized, so the extra goes into the walls); BASE_X never does, because the
charger's long axis runs along Y.

It prints open-top-up, so the only ceilings are the cord port, the escape
port, the LED window and the four foot recesses -- all bridges of 20 mm or
less.  The tie-down holes are through-holes with no ceiling at all.
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Location, Part, Pos,
                       chamfer, fillet)

from dock import measurements as M
from dock import params as P
from dock import tray as T

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
# rear-wall cutters: centred in X, starting at their given Y and Z
_REAR = (Align.CENTER, Align.MIN, Align.MIN)
# -X end-wall cutters: starting at their given X, centred in Y, up from Z
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)
# +X end-wall cutters: ending at their given X, centred in Y and Z
_END_HI = (Align.MAX, Align.CENTER, Align.CENTER)

CABLE_ROOM = 15.0        # plug bodies below the tray plus the cable bend
FENCE_H = 8.0            # charger fence height above the cavity floor
FENCE_CLEAR_Y = 2.0      # minimum cavity clearance beside the fence, per side
CORD_W = 20.0            # AC cord port width (Y)
CORD_H = 16.0            # AC cord port height (Z); its ceiling is a 20 mm bridge
CORD_Z0 = P.FLOOR + 2.0  # cord port sill above the bed
ESCAPE_H = 12.0          # escape port height
LED_W = 4.0              # LED window side
FOOT_R = 5.0             # foot recess radius (Ø10 pads)
FOOT_RECESS_D = 0.6      # leaves 1.0 mm of floor under each foot
FOOT_INSET = 12.0        # foot centre in from each outer face
INLET_PLUG_ROOM = 45.0   # required free X behind the inlet for the C7 cord end
PORT_PLUG_ROOM_MIN = 40.0  # required free X in front of the six USB ports
TIE_D = 4.0              # tie-down hole diameter
TIE_PITCH = 12.0         # tie-down grid pitch
TIE_MARGIN = 6.0         # grid edge in from the fence and the cavity walls

# --- charger pocket ---------------------------------------------------------
# Sized before the box, because a wider charger grows BASE_Y.
# X runs inlet face -> port face; Y runs along the long, six-port face.
POCKET_X = M.CHARGER.port_to_inlet + 2 * P.CLR_FIT
POCKET_Y = M.CHARGER.port_face_width + 2 * P.CLR_FIT
FENCE_X = POCKET_X + 2 * P.WALL
FENCE_Y = POCKET_Y + 2 * P.WALL

# --- the box ----------------------------------------------------------------
REBATE_D = T.TRAY_H
BASE_X = T.TRAY_X + 2 * (P.WALL + P.CLR_FIT)
# The tray sets the floor; a fence that will not fit between the 2*WALL side
# walls with FENCE_CLEAR_Y to spare raises it.  The rebate stays tray-sized,
# so any growth lands in the walls, not in the opening.
BASE_Y = max(T.TRAY_Y + 2 * (P.WALL + P.CLR_FIT),
             FENCE_Y + 2 * FENCE_CLEAR_Y + 4 * P.WALL)
BASE_H = P.FLOOR + M.CHARGER.height + CABLE_ROOM + REBATE_D

# Walls below the rebate are 2*WALL thick, so the rebate leaves a ledge.
CAVITY_X = BASE_X - 4 * P.WALL
CAVITY_Y = BASE_Y - 4 * P.WALL
CAVITY_MIN_X, CAVITY_MAX_X = 2 * P.WALL, BASE_X - 2 * P.WALL
CAVITY_MIN_Y, CAVITY_MAX_Y = -CAVITY_Y / 2, CAVITY_Y / 2
CAVITY_R = P.CORNER_R - 2 * P.WALL   # concentric with the outer CORNER_R

REBATE_X = T.TRAY_X + 2 * P.CLR_FIT
REBATE_Y = T.TRAY_Y + 2 * P.CLR_FIT
REBATE_R = T.OUTER_R + P.CLR_FIT
# The shelf itself.  While BASE_Y is tray-driven the two are equal and the
# ledge is a uniform band; if a wider charger ever grows BASE_Y the Y shelf
# narrows, and the solid-measured ledge test will say so.
LEDGE_W = min((REBATE_X - CAVITY_X) / 2, (REBATE_Y - CAVITY_Y) / 2)
# What the tray actually lands on: its rim is CLR_FIT clear of the rebate
# wall, and its bottom outer edge is chamfered CHAMFER, so that much of the
# shelf sees no flat-on-flat contact.
BEARING_W = LEDGE_W - P.CLR_FIT - P.CHAMFER

# --- fence placement --------------------------------------------------------
# The fence is placed from the +X (port) side: the status LED is on the port
# face and shows through the +X end wall, so the charger sits as close to that
# wall as the USB plugs allow.  The leftover length lands on the inlet side,
# where a cord lying along the floor does not care.
FENCE_CX = CAVITY_MAX_X - PORT_PLUG_ROOM_MIN - POCKET_X / 2
POCKET_MIN_X = FENCE_CX - POCKET_X / 2   # the inlet face of the charger
POCKET_MAX_X = FENCE_CX + POCKET_X / 2   # the port face of the charger
POCKET_MIN_Y = -POCKET_Y / 2
FENCE_MIN_X, FENCE_MAX_X = POCKET_MIN_X - P.WALL, POCKET_MAX_X + P.WALL
# Clearances left over inside the cavity, for the build report.
FENCE_MARGIN_X = CAVITY_X - FENCE_X
FENCE_MARGIN_Y = (CAVITY_Y - FENCE_Y) / 2      # per side, >= FENCE_CLEAR_Y
PORT_PLUG_ROOM = CAVITY_MAX_X - POCKET_MAX_X   # == PORT_PLUG_ROOM_MIN
INLET_ROOM = POCKET_MIN_X - CAVITY_MIN_X       # whatever is left over

# The ports are numbered from the -Y end of the port face, so port 1's centre
# sits at POCKET_MIN_Y + port_face_margin.  On the PowerPort 6 the LED is at
# the *end* of the port row, outboard of port 1 -- away from the other five --
# so the offset is subtracted, toward -Y.
LED_Y = POCKET_MIN_Y + M.CHARGER.port_face_margin - M.CHARGER.led_offset_from_ports

# Escape port: centred on the tray's spare bay, which is the -Y bay of the
# right column, so the cables from it drop straight out of the rear wall.
_SPARE_X0, _, _SPARE_W, _ = T.RIGHT_BAYS["spare"]
ESCAPE_W = P.USB_A_PLUG.width + 4
ESCAPE_CX = P.WALL + P.CLR_FIT + _SPARE_X0 + _SPARE_W / 2
ESCAPE_TOP = BASE_H - REBATE_D - P.WALL        # one wall below the ledge

# Wall cutters span the 2*WALL wall plus a sliver either side, no more.
_WALL_CUT_D = 2 * P.WALL + 0.5
_REAR_CUT_Y0 = -BASE_Y / 2 - 0.25
_END_CUT_X0 = -0.25              # -X end wall: start just outside the face
_END_CUT_X1 = BASE_X + 0.25      # +X end wall: end just outside the face

FOOT_CENTRES: list[tuple[float, float]] = [
    (x, y)
    for x in (FOOT_INSET, BASE_X - FOOT_INSET)
    for y in (-BASE_Y / 2 + FOOT_INSET, BASE_Y / 2 - FOOT_INSET)
]


def _grid_axis(lo: float, hi: float, pitch: float) -> list[float]:
    """As many pitch-spaced centres as fit in [lo, hi], centred in it."""
    n = int(math.floor((hi - lo) / pitch + 1e-9)) + 1
    mid = (lo + hi) / 2
    return [mid + (i - (n - 1) / 2) * pitch for i in range(n)]


def _tie_grid() -> list[tuple[float, float]]:
    """Tie-down hole centres: the free floor between the fence's +X wall and
    the +X cavity wall, full cavity Y, TIE_MARGIN in from each.

    Points that would break into a foot recess are dropped -- a hole there
    would leave 1 mm of floor and a foot that cannot seat flat.
    """
    xs = _grid_axis(FENCE_MAX_X + TIE_MARGIN, CAVITY_MAX_X - TIE_MARGIN, TIE_PITCH)
    ys = _grid_axis(CAVITY_MIN_Y + TIE_MARGIN, CAVITY_MAX_Y - TIE_MARGIN, TIE_PITCH)
    keep_out = FOOT_R + TIE_D / 2 + 1.0
    return [(x, y) for x in xs for y in ys
            if all(math.dist((x, y), c) > keep_out for c in FOOT_CENTRES)]


TIE_GRID: list[tuple[float, float]] = _tie_grid()


def tray_seat() -> Location:
    """Where `tray.build_tray()` goes to seat in the rebate."""
    return Pos(P.WALL + P.CLR_FIT, 0, BASE_H - REBATE_D)


def _rounded_box(sx: float, sy: float, sz: float, r: float, align) -> Part:
    """A box with its four vertical edges filleted to `r`."""
    b = Box(sx, sy, sz, align=align)
    return fillet(b.edges().filter_by(Axis.Z), r) if r > 0 else b


def _fence() -> Part:
    """Raised fence that locates the charger, port face toward +X."""
    fence = Box(FENCE_X, FENCE_Y, FENCE_H + P.FLOOR, align=_MIN)
    fence -= Pos(0, 0, P.FLOOR) * Box(POCKET_X, POCKET_Y, FENCE_H, align=_MIN)
    # fingernail notch through the +Y fence wall, to lift the charger out
    fence -= Pos(0, POCKET_Y / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2, FENCE_H,
                                                 align=_MIN)
    return fence


def build_base() -> Part:
    """The base, underside-down on the bed: X 0..BASE_X, Y centred, Z 0..BASE_H."""
    cx = BASE_X / 2
    body = Pos(cx, 0, 0) * _rounded_box(BASE_X, BASE_Y, BASE_H, P.CORNER_R, _MIN)
    # Downward outer edge of the box: chamfer, never a fillet.  Done before
    # any cavity is cut, so only the outer profile is chamfered.
    body = chamfer(body.faces().sort_by(Axis.Z)[0].edges(), P.CHAMFER)

    # Lower cavity: walls 2*WALL thick, corners concentric with the outer ones.
    body -= Pos(cx, 0, P.FLOOR) * _rounded_box(
        CAVITY_X, CAVITY_Y, BASE_H, CAVITY_R, _MIN)

    # Rebate that receives the tray flush with the rim.
    body -= Pos(cx, 0, BASE_H - REBATE_D) * _rounded_box(
        REBATE_X, REBATE_Y, REBATE_D + 1.0, REBATE_R, _MIN)

    body += Pos(FENCE_CX, 0, 0) * _fence()

    # -X end wall: AC cord port facing the C7 inlet.  A closed rectangular
    # hole, not a notch open to the top: the rim and the rebate ledge stay
    # continuous all round, which is what keeps a 2.4 mm rim stiff.  Its sill
    # is 2 mm above the cavity floor and its 20 mm ceiling is a bridge.
    body -= Pos(_END_CUT_X0, 0, CORD_Z0) * Box(
        _WALL_CUT_D, CORD_W, CORD_H, align=_END_LO)

    # +X end wall: LED window, square, centred on the LED in Y and on the
    # charger's mid-height in Z.
    body -= Pos(_END_CUT_X1, LED_Y, P.FLOOR + M.CHARGER.height / 2) * Box(
        _WALL_CUT_D, LED_W, LED_W, align=_END_HI)

    # Rear (-Y) wall: cable escape port, one wall below the rebate so the
    # ledge stays continuous, centred on the tray's spare bay.
    body -= Pos(ESCAPE_CX, _REAR_CUT_Y0, ESCAPE_TOP - ESCAPE_H) * Box(
        ESCAPE_W, _WALL_CUT_D, ESCAPE_H, align=_REAR)

    # Tie-down grid: through-holes in the floor, so a tie loops from the
    # cavity down under the base and back.
    for x, y in TIE_GRID:
        body -= Pos(x, y, -1.0) * Cylinder(TIE_D / 2, P.FLOOR + 2.0, align=_MIN)

    # Foot recesses: self-adhesive pads sit in them, so the dock does not rock
    # on a squeezed-out bead of adhesive.
    for x, y in FOOT_CENTRES:
        body -= Pos(x, y, 0) * Cylinder(FOOT_R, FOOT_RECESS_D, align=_MIN)
    return body
