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
Y.  Its back is against the -X end wall, as the Trek CHRGtime stands its
own: the mains cord plugs in from outside, through the closed cord port in
that wall, straight into the inlet a POCKET_BACK_SLACK behind it.  There is no
cord room inside the cavity because none is wanted -- the whole run from the
port face to the +X wall is free floor for the plugs and their cables, which
run across the floor to their cutouts in the tray above; the Anker A2154
ships with its own silicone cable-management block, so nothing in the base
routes them.  The device cables leave through an escape port directly above
the cord port in that same wall -- where the CHRGtime puts its own.  A
charger with a status LED gets a window for it in the +X end wall; one
without (the A2154 has no LED at all) leaves that wall blind.  Everything in
here is derived from `measurements.CHARGER`, port pitch included, so
swapping the charger is a measurement change and not a geometry change.

The tray lands flush with the rim, so each end rim carries a finger notch
NOTCH_W wide and NOTCH_D deep to lift it out by.  The notches cut the rim
only: they stop far above the rebate ledge, which stays continuous.

The lower band of the outer wall is a plinth, like the Trek CHRGtime's:
over the bottom PLINTH_H the outer faces lean inward toward the bed, so the
dock reads lighter than a slab and a cable dragged past it meets a sloping
face instead of a square edge.  The taper is shallow enough to print
unsupported, and it takes PLINTH_INSET = WALL off the 2*WALL lower walls, so
they still carry a full WALL where the plinth is thinnest.

Wall stack-up, bottom to top: the shell below the rebate is 2*WALL thick so
the rebate can be cut back to the tray's own footprint and still leave a
continuous ledge all round; above the ledge the rim is WALL thick.  The outer
vertical corners are CORNER_R above the plinth, and CORNER_R less whatever
the plinth has stepped in below it; the cavity corners are CORNER_R - 2*WALL
and the rebate corners the tray's OUTER_R + CLR_FIT -- all three arcs share
a centre, so the ledge is a band of uniform width.  The bottom outer edge
is chamfered, never filleted: it is a downward edge.

BASE_Y grows if a remeasured charger needs a wider fence (the rebate stays
tray-sized, so the extra goes into the walls); BASE_X never does, because the
charger's long axis runs along Y.

It prints open-top-up.  The cord port's ceiling is a plain CORD_W x CORD_H
rectangle: CORD_W is too wide to bridge, so unlike every other ceiling in
the part it prints under a support structure -- SUPPORTED_CEILINGS names it
as the one ceiling the design accepts that for.  Everything else is a
self-supporting bridge of 20 mm or less: the escape port above it
(ESCAPE_W), the LED window when there is one, and the four foot recesses.
The tie-down holes are through-holes with no ceiling at all.
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Location, Part, Plane,
                       Pos, RectangleRounded, Sketch, fillet, loft)

from dock import measurements as M
from dock import params as P
from dock import tray as T

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
# -X end-wall cutters: starting at their given X, centred in Y, up from Z
_END_LO = (Align.MIN, Align.CENTER, Align.MIN)
# +X end-wall cutters: ending at their given X, centred in Y and Z
_END_HI = (Align.MAX, Align.CENTER, Align.CENTER)

CABLE_ROOM = 6.0     # headroom above the charger: only an escape cable crosses it (v2.5: was 15)
FENCE_H = 8.0            # charger fence height above the cavity floor
FENCE_CLEAR_Y = 2.0      # minimum cavity clearance beside the fence, per side
# AC cord port: sized from the moulded C7 end that has to pass through it,
# plus 1 mm of slack per side.  CORD_W is far past the 20 mm bridge
# allowance, so this ceiling cannot print unsupported -- it is the one
# ceiling in the part the design accepts printing with supports under, in
# exchange for a plain rectangular opening (see SUPPORTED_CEILINGS below and
# docs/printing.md).
CORD_W = M.CORD_END.width + 2.0    # port width (Y)
CORD_H = M.CORD_END.height + 2.0   # rectangular part's height (Z)
CORD_TOP = CORD_H                  # total port height: a plain rectangle now
# The opening is centred on the inlet it has to reach, so the moulded cord
# end goes in level rather than being pushed toward the top of the
# rectangle.  Clamped so that a low inlet cannot drive the sill down onto
# the cavity floor or under it.
CORD_Z0_MIN = P.FLOOR + 1.0        # lowest sill worth cutting
CORD_Z0 = max(P.FLOOR + M.CHARGER.inlet_center_z - CORD_H / 2, CORD_Z0_MIN)
# Device-cable escape port: the CHRGtime stacks it directly above the cord
# port in the same wall, so it does too.  It is sized for a device-end plug
# to be posted through, sits 1 mm of wall above the cord port's flat top,
# and its head stops short of the rebate ledge -- it is a closed hole, so
# the ledge and the rim stay continuous.  Its flat ceiling is an ESCAPE_W
# bridge.
ESCAPE_W = P.USB_C_PLUG.width + 5.0   # port width (Y)
ESCAPE_H = 8.0                        # port height (Z), and its bridge
ESCAPE_Z0 = CORD_Z0 + CORD_H + 1.0    # sill, 1 mm above the cord port's flat top
ESCAPE_Z1 = ESCAPE_Z0 + ESCAPE_H      # head, kept clear of the rebate ledge
ESCAPE_LEDGE_GAP_MIN = 1.0            # wall left between the head and the ledge

# The one ceiling in the part that needs print supports: CORD_W is too wide
# for its flat ceiling to bridge, so it is the sole exception to "no
# unsupported ceilings" (see tests/test_base.py and docs/printing.md).
# Everything else is either upward-facing, a through-hole, or a bridge of
# MAX_BRIDGE or less.
SUPPORTED_CEILINGS = ("cord port",)

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
# Nothing places the charger from this any more -- it is backed onto the -X
# wall -- so it is a floor the layout is checked against, not an input.
PORT_PLUG_ROOM_MIN = 40.0  # least free X in front of the six USB ports
# Free X left between the cavity's end wall and the charger's back face,
# the one the AC inlet is on.  `port_to_inlet` is measured to that face, so
# anything standing proud of it -- an inlet shroud, a moulded label boss --
# lives in here; without it such a charger would stand off the end wall and
# never seat in the fence.  See docs/measuring.md.
POCKET_BACK_SLACK = 2.0  # free X behind the charger's back face
TIE_D = 4.0              # tie-down hole diameter
TIE_PITCH = 24.0         # tie-down grid pitch
TIE_MARGIN = 6.0         # grid edge in from the fence and the cavity walls

# --- plinth -----------------------------------------------------------------
# The lower band of the outer wall tapers in toward the bed.  PLINTH_INSET is
# one WALL, so the 2*WALL walls below the rebate still carry a full WALL at
# the plinth's thinnest section -- which is at Z = CHAMFER, the top of the
# elephant-foot chamfer, not at the bed itself.  Below that the chamfer takes
# the outline CHAMFER further in again, exactly as it always did; the bed face
# is therefore PLINTH_INSET + CHAMFER in from the footprint on every side.
PLINTH_H = 12.0          # height of the tapered band above the bed
PLINTH_INSET = P.WALL    # step in at the top of the bottom chamfer
# How far the taper leans off vertical.  Well inside the 45 degrees this part
# holds every downward face to, so the plinth prints without supports.
PLINTH_TAPER_DEG = math.degrees(math.atan2(PLINTH_INSET, PLINTH_H - P.CHAMFER))

# --- charger pocket ---------------------------------------------------------
# Sized before the box, because a wider charger grows BASE_Y.
# X runs inlet face -> port face; Y runs along the long, six-port face.
POCKET_X = M.CHARGER.port_to_inlet + 2 * P.CLR_FIT
POCKET_Y = M.CHARGER.port_face_width + 2 * P.CLR_FIT
# The fence is a U: two ±Y walls and the +X front wall.  The -X side is open,
# because the cavity's own end wall is the charger's back stop.  FENCE_Y still
# has a wall each side, and it is FENCE_Y that can grow BASE_Y; the U's own X
# extent depends on where the cavity wall lands, so FENCE_X waits for it.
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
# The charger is backed onto the -X end wall, the way the CHRGtime manual
# shows the supply standing: the cord plugs in from outside, through the wall
# and straight into the inlet, so no floor is spent behind it.  The cavity's
# inner wall face is the back stop; the pocket starts POCKET_BACK_SLACK off
# it, room for whatever stands proud of the charger's back face, and
# everything from the port face to the +X wall is free floor.
POCKET_MIN_X = CAVITY_MIN_X + POCKET_BACK_SLACK  # the charger's back face
POCKET_MAX_X = POCKET_MIN_X + POCKET_X   # the port face of the charger
POCKET_MIN_Y = -POCKET_Y / 2
FENCE_CX = POCKET_MIN_X + POCKET_X / 2   # the pocket's centre, not the U's
# The U's side walls run back to a hair (CLR_FIT) off the cavity wall, so
# they reach behind the pocket and guide the charger the whole way in.
FENCE_MIN_X, FENCE_MAX_X = CAVITY_MIN_X + P.CLR_FIT, POCKET_MAX_X + P.WALL
FENCE_X = FENCE_MAX_X - FENCE_MIN_X
# Clearances left over inside the cavity, for the build report.
FENCE_MARGIN_X = CAVITY_MAX_X - FENCE_MAX_X    # free floor in front of the U
FENCE_MARGIN_Y = (CAVITY_Y - FENCE_Y) / 2      # per side, >= FENCE_CLEAR_Y
PORT_PLUG_ROOM = CAVITY_MAX_X - POCKET_MAX_X   # >= PORT_PLUG_ROOM_MIN

# The ports are numbered from the -Y end of the port face, so port 1's centre
# sits at POCKET_MIN_Y + port_face_margin.  Where there is an LED it is at
# the *end* of the port row, outboard of port 1 -- away from the other five
# -- so the offset is subtracted, toward -Y.
PORT_Y1 = POCKET_MIN_Y + M.CHARGER.port_face_margin
LED_Y = (PORT_Y1 - M.CHARGER.led_offset_from_ports) if HAS_LED else None

# The six port centres, from port 1 at PORT_Y1 to port 6 on the port pitch:
# test data for checking a plug at every port clears the base, and for the
# LED offset above.
PORT_PITCH = M.CHARGER.port_pitch   # centre to centre along the port face
PORT_YS: list[float] = [PORT_Y1 + i * PORT_PITCH for i in range(6)]

# Wall cutters span the 2*WALL wall plus a sliver either side, no more.
_WALL_CUT_D = 2 * P.WALL + 0.5
# The plinth only ever moves an outer face inward, so a cutter that starts
# 0.25 mm outside the nominal footprint starts outside the tapered face too,
# wherever in the band it crosses it -- and it still has to reach the cavity
# wall at the far end, which is what _WALL_CUT_D is measured for.
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


def _tie_grid() -> list[tuple[float, float]]:
    """Tie-down hole centres: the free floor in front of the charger, from
    the fence's +X wall out to the +X cavity wall, full cavity Y, TIE_MARGIN
    in from each.

    That includes the strip between the fence and the plugs standing in
    front of the port face, and where the Roam's cable turns back toward its
    own end of the dock: a tie is worth having there too, not only further
    out.

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


def _plinth_profile(inset: float, z: float) -> Sketch:
    """The outer outline at height `z`, `inset` in from the nominal footprint
    on every side, centred on X = Y = 0.

    The corner radius shrinks with the inset, so every arc keeps the same
    centre and the taper runs smoothly through the corners instead of
    pinching them.
    """
    return Plane.XY.offset(z) * RectangleRounded(
        BASE_X - 2 * inset, BASE_Y - 2 * inset, P.CORNER_R - inset)


def _outer_body() -> Part:
    """The base's outer solid, centred on X = Y = 0 and standing up from the
    bed: a plinth for the bottom PLINTH_H, the plain rounded box above it.

    A ruled loft through three concentric outlines, so the walls taper on a
    plane and the corners on a cone.  The bottom segment, from the bed to
    Z = CHAMFER, is the elephant-foot chamfer: built into the loft rather
    than chamfered onto the finished edge, because an equal-distance chamfer
    taken off a leaning wall comes out steeper than 45 degrees, and every
    downward face in this part is held to 45.  As the loft has it, that face
    is exactly 45 -- CHAMFER in over CHAMFER up -- and the taper above it is
    PLINTH_TAPER_DEG.
    """
    plinth = loft([_plinth_profile(PLINTH_INSET + P.CHAMFER, 0.0),
                   _plinth_profile(PLINTH_INSET, P.CHAMFER),
                   _plinth_profile(0.0, PLINTH_H)], ruled=True)
    return plinth + Pos(0, 0, PLINTH_H) * _rounded_box(
        BASE_X, BASE_Y, BASE_H - PLINTH_H, P.CORNER_R, _MIN)


def _cord_cutter(depth: float) -> Part:
    """The AC cord port's cutter: a plain CORD_W x CORD_H rectangular
    opening, lying on Z = 0 and running `depth` along +X from X = 0.

    CORD_W is well past MAX_BRIDGE, so this ceiling cannot print
    unsupported; it is the one ceiling in SUPPORTED_CEILINGS, and prints
    with a support structure under it rather than dodging the bridge with a
    peaked roof.
    """
    return Box(depth, CORD_W, CORD_H, align=_END_LO)


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
    """Raised fence that locates the charger, port face toward +X, built in
    base coordinates.

    A U, not a ring: the charger backs onto the -X cavity wall, so that wall
    is the fourth side and the fence carries only the two ±Y walls and the
    +X front wall.  The side walls stop a hair's breadth (CLR_FIT) short of
    the cavity wall rather than running into it.  That gap is not a fit
    clearance and nothing seats in it: it is there so the U stays its own
    solid, which is how every fence test finds and measures it.  The slicer
    fuses it back into the wall, harmlessly -- the U is fused to the floor
    slab along its whole length either way.  The fingernail notch stays in
    the +Y wall.
    """
    fence = Pos(FENCE_MIN_X, 0, 0) * Box(
        FENCE_X, FENCE_Y, FENCE_H + P.FLOOR, align=_END_LO)
    # the pocket, cut open toward -X so the cavity wall closes it
    fence -= Pos(FENCE_MIN_X - 1.0, 0, P.FLOOR) * Box(
        POCKET_MAX_X - FENCE_MIN_X + 1.0, POCKET_Y, FENCE_H, align=_END_LO)
    # fingernail notch through the +Y fence wall, to lift the charger out
    fence -= Pos(FENCE_CX, POCKET_Y / 2, P.FLOOR) * Box(20, 2 * P.WALL + 2,
                                                        FENCE_H, align=_MIN)
    return fence


def build_base() -> Part:
    """The base, underside-down on the bed: X 0..BASE_X, Y centred, Z 0..BASE_H."""
    cx = BASE_X / 2
    # Outer profile complete before anything is cut out of it: the plinth's
    # taper and the bottom chamfer are both in _outer_body(), so only the
    # outer profile carries them.
    body = Pos(cx, 0, 0) * _outer_body()

    # Lower cavity: walls 2*WALL thick, corners concentric with the outer ones.
    body -= Pos(cx, 0, P.FLOOR) * _rounded_box(
        CAVITY_X, CAVITY_Y, BASE_H, CAVITY_R, _MIN)

    # Rebate that receives the tray flush with the rim.
    body -= Pos(cx, 0, BASE_H - REBATE_D) * _rounded_box(
        REBATE_X, REBATE_Y, REBATE_D + 1.0, REBATE_R, _MIN)

    body += _fence()

    # -X end wall: AC cord port facing the mains inlet.  A closed hole, not a
    # notch open to the top: the rim and the rebate ledge stay continuous all
    # round, which is what keeps a 2.4 mm rim stiff.  Its rectangular opening
    # is centred on the inlet's height; its flat ceiling is the one ceiling
    # in the part printed with supports (SUPPORTED_CEILINGS).
    body -= Pos(_END_CUT_X0, 0, CORD_Z0) * _cord_cutter(_WALL_CUT_D)

    # +X end wall: LED window, centred on the LED in Y and on the charger's
    # mid-height in Z.  Skipped outright on a charger with no LED -- that
    # wall stays blind rather than carrying a hole onto nothing.
    if HAS_LED:
        body -= Pos(_END_CUT_X1, LED_Y, P.FLOOR + M.CHARGER.height / 2) * Box(
            _WALL_CUT_D, LED_W, LED_H, align=_END_HI)

    # -X end wall again, directly above the cord port: the device-cable
    # escape port.  Its sill clears the cord port's flat top by 1 mm and its
    # head stops ESCAPE_LEDGE_GAP_MIN below the rebate ledge, so this is a
    # closed hole like the cord port and the ledge stays continuous.
    body -= Pos(_END_CUT_X0, 0, ESCAPE_Z0) * Box(
        _WALL_CUT_D, ESCAPE_W, ESCAPE_H, align=_END_LO)

    # Lift-out notches: the tray sits flush with the rim, so a finger notch
    # at each end is the only way to get hold of it.  They cut the rim only
    # -- NOTCH_D stops well above the rebate ledge, which stays unbroken.
    for x0 in (_END_CUT_X0, _END_CUT_X1 - _RIM_CUT_D):
        body -= Pos(x0, 0, BASE_H - NOTCH_D) * _notch_cutter(_RIM_CUT_D)

    # Tie-down grid: through-holes in the floor, so a tie threads from the
    # cavity down under the base and back up.
    for x, y in TIE_GRID:
        body -= Pos(x, y, -1.0) * Cylinder(TIE_D / 2, P.FLOOR + 2.0, align=_MIN)

    # Foot recesses: self-adhesive pads sit in them, so the dock does not rock
    # on a squeezed-out bead of adhesive.
    for x, y in FOOT_CENTRES:
        body -= Pos(x, y, 0) * Cylinder(FOOT_R, FOOT_RECESS_D, align=_MIN)
    return body
