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
    assert base.CH_W + 2 * params.WALL < base.CAVITY_Y
    assert base.CH_L > m.CHARGER.length and base.CH_W > m.CHARGER.width


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


def test_deck_seats_in_the_rebate_without_interference():
    p = base.build_base()
    seated = base.deck_seat() * deck.build_deck()
    assert (seated & p).volume < 1e-3
