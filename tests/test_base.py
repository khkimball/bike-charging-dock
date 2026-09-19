from build123d import Axis

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


def test_charger_pocket_fits_inside_the_lower_cavity():
    """The fence's charger pocket must sit wholly inside the base cavity."""
    assert base.CH_L > m.CHARGER.length
    assert base.CH_W > m.CHARGER.width
    assert base.POCKET_MIN_X > base.CAVITY_MIN_X
    assert base.POCKET_MAX_X < base.CAVITY_MAX_X
    assert base.CH_W / 2 < base.CAVITY_Y / 2
    # the fence walls themselves must clear the cavity too
    assert base.CH_L + 2 * params.WALL <= base.CAVITY_X
    assert base.CH_W + 2 * params.WALL < base.CAVITY_Y
