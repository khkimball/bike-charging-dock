"""Base: the rounded-corner lower box.  It hides the charger and the cable
slack, and the tray drops into a rebate in its top rim.

The base has its own origin: the box spans X = 0..BASE_X, is centred on Y,
and its underside is the build-plate face at Z = 0.  The tray has its own
origin too, and the two do NOT coincide -- the rebate is inset from the base
rim, so the tray must be moved by `tray_seat()` to sit in it.  Both parts
print underside-down on their own origins; `tray_seat()` is for assembly
views and fit checks only.

Charger orientation: the charger lies flat with its long, six-port face
running along Y.  The ports look toward +X and the mains inlet looks toward
-X, so the pocket is `port_to_inlet` deep in X and `port_face_width` long in
Y.  The mains cord leaves through a closed port in the -X end wall, and the
device cables leave through an escape port directly above the cord port in
that same wall -- where the Trek CHRGtime puts its own.  A charger with a
status LED gets a window for it in the +X end wall; one without (the A2154
has no LED at all) leaves that wall blind.  Everything in here is derived
from `measurements.CHARGER`, port pitch included, so swapping the charger is
a measurement change and not a geometry change.

The CHRGtime also runs a bar under its tray for the device cables to pass
beneath, so they leave the charger in a tidy row instead of a knot.  A single
bar would have to bridge the whole width of the cavity, 150 mm and more, so
the bar is broken into a row of inverted-U cable loops, one per charger port,
standing on the cavity floor beyond the plugs: each has a LOOP_W_IN crown,
short enough to print unsupported in place.

The tray lands flush with the rim, so each end rim carries a finger notch
NOTCH_W wide and NOTCH_D deep to lift it out by.  The notches cut the rim
only: they stop far above the rebate ledge, which stays continuous.

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

It prints open-top-up.  The cord port is too wide to bridge, so its roof is
a 45 degree peak; the only remaining ceilings are the escape port above it
(ESCAPE_W), the crown of each cable loop (LOOP_W_IN), the LED window when
there is one, and the four foot recesses -- all bridges of 20 mm or less.
The tie-down holes are through-holes with no ceiling at all.
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Location, Part, Plane,
                       Polyline, Pos, chamfer, extrude, fillet, make_face)

from dock import measurements as M
from dock import params as P
from dock import tray as T

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
# -X end-wall cutters: starting at their given X, centred in Y, up from Z
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)
# +X end-wall cutters: ending at their given X, centred in Y and Z
_END_HI = (Align.MAX, Align.CENTER, Align.CENTER)

CABLE_ROOM = 15.0        # plug bodies below the tray plus the cable bend
FENCE_H = 8.0            # charger fence height above the cavity floor
FENCE_CLEAR_Y = 2.0      # minimum cavity clearance beside the fence, per side
# AC cord port: sized from the moulded C7 end that has to pass through it,
# plus 1 mm of slack per side.  CORD_W is far past the 20 mm bridge
# allowance, so the port is not a rectangle: a 45 degree peak of CORD_W / 2
# sits on top of the rectangular opening, giving a self-supporting roof.
CORD_W = M.CORD_END.width + 2.0    # port width (Y)
CORD_H = M.CORD_END.height + 2.0   # rectangular part's height (Z)
CORD_PEAK = CORD_W / 2             # 45 degree roof above it
CORD_TOP = CORD_H + CORD_PEAK      # total port height
# The opening is centred on the inlet it has to reach, so the moulded cord
# end goes in level rather than being pushed up toward the ridge, where the
# port is already narrowing.  Clamped so that a low inlet cannot drive the
# sill down onto the cavity floor or under it.
CORD_Z0_MIN = P.FLOOR + 1.0        # lowest sill worth cutting
CORD_Z0 = max(P.FLOOR + M.CHARGER.inlet_center_z - CORD_H / 2, CORD_Z0_MIN)
# Device-cable escape port: the CHRGtime stacks it directly above the cord
# port in the same wall, so it does too.  It is sized for a device-end plug
# to be posted through, sits 1 mm of wall above the cord roof's peak, and its
# head stops short of the rebate ledge -- it is a closed hole, so the ledge
# and the rim stay continuous.  Its flat ceiling is an ESCAPE_W bridge.
ESCAPE_W = P.USB_C_PLUG.width + 5.0   # port width (Y)
ESCAPE_H = 8.0                        # port height (Z), and its bridge
ESCAPE_Z0 = CORD_Z0 + CORD_TOP + 1.0  # sill, one wall above the cord peak
ESCAPE_Z1 = ESCAPE_Z0 + ESCAPE_H      # head, kept clear of the rebate ledge
ESCAPE_LEDGE_GAP_MIN = 1.0            # wall left between the head and the ledge
# Finger notches in the rim, one at each end, for lifting the tray out: the
# tray sits flush with the rim, so without them there is nothing to grip.
NOTCH_W = 40.0           # notch width (Y), a two-finger grip
NOTCH_D = 15.0           # how far down from the rim it cuts
NOTCH_R = 5.0            # its bottom corners, rounded so the rim cannot split
# LED window: wider than it is tall.  The LED's position along the port face
# is the least certain measurement on a charger that has one, so the window
# is widened in Y to catch it and kept short in Z, where its ceiling has to
# bridge.  Cut only when HAS_LED; there is no point putting a hole in the
# +X end wall of a dock whose charger has nothing to show through it.
HAS_LED = M.CHARGER.led_offset_from_ports is not None
LED_W = 8.0              # window width (Y)
LED_H = 4.0              # window height (Z), and its bridge
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
# The fence is placed from the +X (port) side: the plugs are what needs the
# room, so the charger sits as close to that wall as they allow and the
# leftover length lands on the inlet side, where a cord lying along the floor
# does not care.  It keeps a status LED, which is on the port face, near its
# window too, on a charger that has one.
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
# sits at POCKET_MIN_Y + port_face_margin.  Where there is an LED it is at
# the *end* of the port row, outboard of port 1 -- away from the other five
# -- so the offset is subtracted, toward -Y.
PORT_Y1 = POCKET_MIN_Y + M.CHARGER.port_face_margin
LED_Y = (PORT_Y1 - M.CHARGER.led_offset_from_ports) if HAS_LED else None

# --- cable loops ------------------------------------------------------------
# One inverted U per charger port, standing on the cavity floor, for a cable
# to route under on its way to the tray's cutout.  The opening passes a
# cable, not a plug, and the crown is a LOOP_W_IN bridge the printer crosses
# unsupported.
#
# LOOP_STANDOFF runs from the fence's +X wall to the row's CENTRELINE, not
# to its face, because that is what LOOP_XC is.  The clearances that matter
# are therefore one half-thickness shorter:
#
#     past the fence wall   LOOP_STANDOFF - LOOP_T / 2
#     past a plugged-in end P.WALL + LOOP_STANDOFF - LOOP_T / 2
#                           - P.USB_A_PLUG.length
#
# and it is the second one that sets it.  Six overmolds stand in front of
# the port face, so a row nearer than their length is a row you cannot plug
# a cable in through; the spare beyond that is room for the cable to turn
# down out of the plug.  test_base.py measures both gaps on the solid.
#
# The loops are on the port pitch, which is narrower than a loop is wide, so
# each one merges into its neighbours: the row prints as one bar with a
# window over every port, which is what the CHRGtime's bar does anyway.
PORT_PITCH = M.CHARGER.port_pitch   # centre to centre along the port face
LOOP_W_IN = 10.0         # inner opening width (Y), and the crown's bridge
LOOP_H_IN = 12.0         # inner opening height (Z)
LOOP_T = 3.0             # loop thickness along X
LOOP_STANDOFF = 24.0     # fence wall to the loop row's centreline
LOOP_XC = POCKET_MAX_X + P.WALL + LOOP_STANDOFF     # clear of the plug bodies
LOOP_HALF_W = LOOP_W_IN / 2 + LOOP_T                # loop half width in Y
# One loop per port, on the port centres themselves.
LOOP_YS: list[float] = [PORT_Y1 + i * PORT_PITCH for i in range(6)]
TIE_LOOP_CLEAR = 2.0     # floor left between a tie hole and a loop foot

# Wall cutters span the 2*WALL wall plus a sliver either side, no more.
_WALL_CUT_D = 2 * P.WALL + 0.5
_END_CUT_X0 = -0.25              # -X end wall: start just outside the face
_END_CUT_X1 = BASE_X + 0.25      # +X end wall: end just outside the face
# Rim cutters go through the WALL-thick rim and a sliver into the rebate.
_RIM_CUT_D = P.WALL + 0.5

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


def _clears_the_loops(x: float, y: float) -> bool:
    """Is a tie hole at (x, y) clear of the cable loops standing on the same
    floor, by TIE_LOOP_CLEAR of material?

    The loop row is a band: LOOP_T wide in X, and in Y it runs from the first
    loop's outer face to the last one's.  A hole outside either span is fine,
    so the grid keeps its whole middle column at the ends of the cavity where
    the row does not reach.
    """
    if abs(x - LOOP_XC) >= LOOP_T / 2 + TIE_D / 2 + TIE_LOOP_CLEAR:
        return True
    reach = LOOP_HALF_W + TIE_D / 2 + TIE_LOOP_CLEAR
    return not (LOOP_YS[0] - reach < y < LOOP_YS[-1] + reach)


def _tie_grid() -> list[tuple[float, float]]:
    """Tie-down hole centres: the free floor between the fence's +X wall and
    the +X cavity wall, full cavity Y, TIE_MARGIN in from each.

    Points that would break into a foot recess are dropped -- a hole there
    would leave 1 mm of floor and a foot that cannot seat flat.  So are the
    points the cable loops stand on, or stand too near: that costs the middle
    column everywhere the loop row reaches, and leaves the grid running down
    both sides of the row.
    """
    xs = _grid_axis(FENCE_MAX_X + TIE_MARGIN, CAVITY_MAX_X - TIE_MARGIN, TIE_PITCH)
    ys = _grid_axis(CAVITY_MIN_Y + TIE_MARGIN, CAVITY_MAX_Y - TIE_MARGIN, TIE_PITCH)
    keep_out = FOOT_R + TIE_D / 2 + 1.0
    return [(x, y) for x in xs for y in ys
            if all(math.dist((x, y), c) > keep_out for c in FOOT_CENTRES)
            and _clears_the_loops(x, y)]


TIE_GRID: list[tuple[float, float]] = _tie_grid()


def tray_seat() -> Location:
    """Where `tray.build_tray()` goes to seat in the rebate."""
    return Pos(P.WALL + P.CLR_FIT, 0, BASE_H - REBATE_D)


def _rounded_box(sx: float, sy: float, sz: float, r: float, align) -> Part:
    """A box with its four vertical edges filleted to `r`."""
    b = Box(sx, sy, sz, align=align)
    return fillet(b.edges().filter_by(Axis.Z), r) if r > 0 else b


def _cord_cutter(depth: float) -> Part:
    """The AC cord port's cutter: a CORD_W x CORD_H opening under a 45 degree
    peak, lying on Z = 0 and running `depth` along +X from X = 0.

    The peak is what makes the port printable.  A CORD_W-wide flat ceiling
    would be a bridge half as long again as the printer will cross; two 45
    degree planes meeting at a ridge are the steepest roof it needs no
    support for at all.
    """
    half = CORD_W / 2
    section = Plane.YZ * make_face(Polyline(
        (-half, 0), (half, 0), (half, CORD_H), (0, CORD_TOP), (-half, CORD_H),
        close=True))
    return extrude(section, amount=depth)


def _notch_cutter(depth: float) -> Part:
    """A lift-out notch's cutter: NOTCH_W wide, NOTCH_D tall with its two
    bottom corners rounded to NOTCH_R, lying on Z = 0 and running `depth`
    along +X from X = 0.

    The rounded bottom keeps the cut from ending in a sharp inside corner,
    which in a WALL-thick rim is where a crack would start.  Rounding it on
    the cutter leaves the material convex there, and the notch floor faces
    up, so nothing new overhangs.
    """
    cutter = Box(depth, NOTCH_W, NOTCH_D, align=_END_LO)
    bottom = cutter.edges().filter_by(Axis.X).group_by(Axis.Z)[0]
    return fillet(bottom, NOTCH_R)


def _fence() -> Part:
    """Raised fence that locates the charger, port face toward +X."""
    fence = Box(FENCE_X, FENCE_Y, FENCE_H + P.FLOOR, align=_MIN)
    fence -= Pos(0, 0, P.FLOOR) * Box(POCKET_X, POCKET_Y, FENCE_H, align=_MIN)
    # fingernail notch through the +Y fence wall, to lift the charger out
    fence -= Pos(0, POCKET_Y / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2, FENCE_H,
                                                 align=_MIN)
    return fence


def _loop_row() -> Part:
    """The whole row of cable loops, standing on Z = 0 and centred on X:
    LOOP_T thick, one inverted U per port centre in LOOP_YS.

    Every crown is a LOOP_W_IN bridge, well inside the 20 mm the printer
    crosses unsupported, so the row prints in place with the base.

    The outers are fused first and the windows cut afterwards, which matters
    whenever the port pitch is narrower than a loop is wide: the outers then
    overlap, and cutting last is what keeps every window the full LOOP_W_IN.
    Fusing finished loops instead would let each one's leg grow into its
    neighbour's window.  What is left between two windows is a post
    PORT_PITCH - LOOP_W_IN thick, which has to stay at least a wall thick --
    there is a test that measures it on the solid.
    """
    row = Part()
    for y in LOOP_YS:
        row += Pos(0, y, 0) * Box(LOOP_T, 2 * LOOP_HALF_W, LOOP_H_IN + LOOP_T,
                                  align=_MIN)
    for y in LOOP_YS:
        row -= Pos(0, y, 0) * Box(LOOP_T + 2, LOOP_W_IN, LOOP_H_IN, align=_MIN)
    return row


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

    # Cable loops, one per charger port, fused to the cavity floor beyond the
    # plugs standing in front of the port face: each device cable drops out
    # of its plug, runs under its loop and up through its bay's cutout in the
    # tray.
    body += Pos(LOOP_XC, 0, P.FLOOR) * _loop_row()

    # -X end wall: AC cord port facing the mains inlet.  A closed hole, not a
    # notch open to the top: the rim and the rebate ledge stay continuous all
    # round, which is what keeps a 2.4 mm rim stiff.  Its rectangular opening
    # is centred on the inlet's height and its roof is a 45 degree peak, not
    # a bridge.
    body -= Pos(_END_CUT_X0, 0, CORD_Z0) * _cord_cutter(_WALL_CUT_D)

    # +X end wall: LED window, centred on the LED in Y and on the charger's
    # mid-height in Z.  Skipped outright on a charger with no LED -- that
    # wall stays blind rather than carrying a hole onto nothing.
    if HAS_LED:
        body -= Pos(_END_CUT_X1, LED_Y, P.FLOOR + M.CHARGER.height / 2) * Box(
            _WALL_CUT_D, LED_W, LED_H, align=_END_HI)

    # -X end wall again, directly above the cord port: the device-cable
    # escape port.  Its sill clears the cord roof's peak by 1 mm and its head
    # stops ESCAPE_LEDGE_GAP_MIN below the rebate ledge, so this is a closed
    # hole like the cord port and the ledge stays continuous.
    body -= Pos(_END_CUT_X0, 0, ESCAPE_Z0) * Box(
        _WALL_CUT_D, ESCAPE_W, ESCAPE_H, align=_END_LO)

    # Lift-out notches: the tray sits flush with the rim, so a finger notch
    # at each end is the only way to get hold of it.  They cut the rim only
    # -- NOTCH_D stops well above the rebate ledge, which stays unbroken.
    for x0 in (_END_CUT_X0, _END_CUT_X1 - _RIM_CUT_D):
        body -= Pos(x0, 0, BASE_H - NOTCH_D) * _notch_cutter(_RIM_CUT_D)

    # Tie-down grid: through-holes in the floor, so a tie loops from the
    # cavity down under the base and back.
    for x, y in TIE_GRID:
        body -= Pos(x, y, -1.0) * Cylinder(TIE_D / 2, P.FLOOR + 2.0, align=_MIN)

    # Foot recesses: self-adhesive pads sit in them, so the dock does not rock
    # on a squeezed-out bead of adhesive.
    for x, y in FOOT_CENTRES:
        body -= Pos(x, y, 0) * Cylinder(FOOT_R, FOOT_RECESS_D, align=_MIN)
    return body
