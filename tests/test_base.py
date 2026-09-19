import math

from build123d import Axis, Box, Align, Pos

from dock import base, deck, params
from dock import measurements as m


def test_base_outer_size_wraps_deck_with_clearance():
    bb = base.build_base().bounding_box().size
    assert abs(bb.X - (deck.DECK_X + 2 * (params.WALL + params.CLR_FIT))) < 1e-6
    assert abs(bb.Y - (deck.DECK_Y + 2 * (params.WALL + params.CLR_FIT))) < 1e-6


def test_base_height_leaves_charger_room_under_plate():
    assert base.BASE_H >= params.FLOOR + m.CHARGER.height + deck.PLATE_T


def test_rebate_depth_matches_plate():
    assert abs(base.REBATE_D - deck.PLATE_T) < 1e-6


def test_base_valid_and_on_bed():
    p = base.build_base()
    assert p.is_valid
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_base_has_four_foot_recesses():
    p = base.build_base()
    bottom = p.faces().sort_by(Axis.Z)[0]
    assert len(bottom.inner_wires()) == 4


def test_rebate_opening_matches_deck_plus_fit_clearance():
    """The ledge the plate lands on is bounded by the rebate opening."""
    p = base.build_base()
    z = base.BASE_H - base.REBATE_D
    ledge = [f for f in p.faces().filter_by(Axis.Z)
             if abs(f.center().Z - z) < 1e-6 and f.normal_at().Z > 0]
    assert ledge, "no horizontal ledge face at the bottom of the rebate"
    xs = [v for f in ledge for v in (f.bounding_box().min.X, f.bounding_box().max.X)]
    ys = [v for f in ledge for v in (f.bounding_box().min.Y, f.bounding_box().max.Y)]
    assert abs((max(xs) - min(xs)) - (deck.DECK_X + 2 * params.CLR_FIT)) < 1e-6
    assert abs((max(ys) - min(ys)) - (deck.DECK_Y + 2 * params.CLR_FIT)) < 1e-6


_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)


def _slab(p, z):
    """Horizontal 0.2 mm cross-section of the part at height z."""
    probe = Pos(base.BASE_X / 2, 0, z) * Box(2 * base.BASE_X, 2 * base.BASE_Y,
                                             0.2, align=_CTR)
    return p & probe


def _cavity_bbox(p):
    """Measure the lower cavity off the solid, at a height clear of every
    cut-out and above the fence."""
    z = params.FLOOR + base.FENCE_H + 2.0
    ring = _slab(p, z)
    top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    inner = top.inner_wires()
    assert len(inner) == 1, f"expected one cavity opening, found {len(inner)}"
    return inner[0].bounding_box()


def _fence_section(p):
    """The fence's cross-section, measured off the solid at mid-fence height."""
    z = params.FLOOR + base.FENCE_H / 2
    solids = _slab(p, z).solids()
    assert len(solids) == 2, f"fence should stand free of the walls, got {len(solids)}"
    return min(solids, key=lambda s: s.bounding_box().size.X)


def _pocket_port_face_x(p):
    """X of the charger's port face, measured off the fence cross-section."""
    fence = _fence_section(p)
    return max(f.center().X for f in fence.faces().filter_by(Axis.X)
               if f.normal_at().X < 0)


def _led_window_bbox(p):
    """The single hole in the +X end wall, measured off the solid."""
    outer = max((f for f in p.faces().filter_by(Axis.X) if f.normal_at().X > 0),
                key=lambda f: f.center().X)
    inner = outer.inner_wires()
    assert len(inner) == 1, "expected exactly one hole in the +X end wall"
    return inner[0].bounding_box()


def test_charger_pocket_fits_inside_the_lower_cavity():
    """Measured on the solid: the fence sits wholly inside the lower cavity."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    fence = _fence_section(p).bounding_box()
    assert fence.min.X > cav.min.X
    assert fence.max.X < cav.max.X
    assert fence.min.Y > cav.min.Y
    assert fence.max.Y < cav.max.Y
    # tripwire on a wider charger than the nominal A2123
    assert base.POCKET_Y + 2 * params.WALL < base.CAVITY_Y
    assert base.POCKET_X > m.CHARGER.port_to_inlet
    assert base.POCKET_Y > m.CHARGER.port_face_width


def test_room_in_front_of_the_charger_inlet_for_the_cord():
    """Measured on the solid: free X between the cavity wall and the pocket's
    inlet face is at least INLET_PLUG_ROOM."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    fence = _fence_section(p)
    # inward-facing (+X normal) faces of the fence section; the lowest is the
    # pocket's -X face, i.e. where the charger's inlet sits
    pocket_min_x = min(f.center().X for f in fence.faces().filter_by(Axis.X)
                       if f.normal_at().X > 0)
    assert pocket_min_x - cav.min.X >= base.INLET_PLUG_ROOM - 1e-6


def test_room_in_front_of_the_charger_ports_for_the_plugs():
    """Measured on the solid: free X between the pocket's port face and the
    cavity wall, where six USB-A plugs and their bend radius have to live."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    # the pocket's +X face is where the charger's six ports sit
    pocket_max_x = _pocket_port_face_x(p)
    assert cav.max.X - pocket_max_x >= base.PORT_PLUG_ROOM_MIN - 1e-6


def test_cord_notch_is_in_the_minus_x_end_wall_at_the_inlet():
    """Measured on the solid: at the inlet centre height the -X end wall is
    open over CORD_W, centred on the charger."""
    p = base.build_base()
    ring = _slab(p, params.FLOOR + m.CHARGER.inlet_center_z + 1.0)
    # the -X wall is split in two by the notch
    left = [f for f in ring.faces().filter_by(Axis.Y)
            if f.center().X < base.CAVITY_MIN_X and abs(f.normal_at().Y) > 0.99]
    ys = sorted(f.center().Y for f in left)
    assert ys, "no notch cheeks in the -X end wall"
    assert abs((max(ys) - min(ys)) - base.CORD_W) < 1e-6
    assert abs((max(ys) + min(ys)) / 2) < 1e-6


def test_led_window_is_in_the_plus_x_end_wall_beside_the_first_port():
    """Measured on the solid: a LED_W square hole through the +X end wall,
    centred on the charger's mid-height and on the LED offset in Y."""
    p = base.build_base()
    bb = _led_window_bbox(p)
    assert abs(bb.size.Y - base.LED_W) < 1e-6
    assert abs(bb.size.Z - base.LED_W) < 1e-6
    assert abs(bb.center().Y - base.LED_Y) < 1e-6
    assert abs(bb.center().Z - (params.FLOOR + m.CHARGER.height / 2)) < 1e-6
    assert base.POCKET_MIN_Y < base.LED_Y < base.POCKET_MIN_Y + base.POCKET_Y


# An LED shining down a long air gap lights the whole cavity instead of the
# window; keep the window within a hand's width of the LED itself.
MAX_LED_THROW = 45.0


def test_led_window_is_close_enough_to_the_led_to_see_it():
    """Measured on the solid: the fence is placed from the +X side, so the
    charger's port face (which carries the LED) is near the +X end wall."""
    p = base.build_base()
    throw = _led_window_bbox(p).center().X - _pocket_port_face_x(p)
    assert 0 < throw <= MAX_LED_THROW, (
        f"LED window is {throw:.1f} mm from the port face")


def test_led_window_is_outboard_of_the_first_port():
    """Measured on the solid: the PowerPort 6's LED is at the end of the port
    row, away from the other five -- so the window sits between the pocket's
    -Y edge and port 1, not inboard of it."""
    p = base.build_base()
    y = _led_window_bbox(p).center().Y
    port_one_y = base.POCKET_MIN_Y + m.CHARGER.port_face_margin
    assert y < port_one_y, "LED window is inboard of port 1"
    assert base.POCKET_MIN_Y <= y <= base.POCKET_MIN_Y + base.POCKET_Y


def test_escape_port_stays_in_the_rear_wall():
    p = base.build_base()
    rear = min((f for f in p.faces().filter_by(Axis.Y)
                if f.normal_at().Y < 0), key=lambda f: f.center().Y)
    inner = rear.inner_wires()
    assert len(inner) == 1
    bb = inner[0].bounding_box()
    assert abs(bb.size.Z - base.ESCAPE_H) < 1e-6


def test_deck_seats_in_the_rebate_without_interference():
    p = base.build_base()
    seated = base.deck_seat() * deck.build_deck()
    assert (seated & p).volume < 1e-3


MAX_BRIDGE = 20.0   # a ceiling this short prints unsupported

# The base prints open-top-up, so its only ceilings are the rear escape port,
# the LED window in the +X end wall, and the four foot recesses.  Every other
# downward face has to be within 45 deg of vertical.
def test_no_unsupported_ceilings_in_the_base():
    p = base.build_base()
    bed_z = p.bounding_box().min.Z
    for f in p.faces():
        if f.area <= 0:
            continue
        n = f.normal_at(f.center())
        if n.Z >= -1e-6:
            continue
        if abs(f.center().Z - bed_z) < 1e-6:
            continue                      # the bed face itself
        overhang = math.degrees(math.asin(min(1.0, -n.Z)))
        if overhang <= 45.0 + 1e-6:
            continue
        bb = f.bounding_box().size
        assert max(bb.X, bb.Y) <= MAX_BRIDGE, (
            f"{overhang:.1f} deg ceiling spanning {max(bb.X, bb.Y):.1f} mm "
            f"at {f.center()}")
