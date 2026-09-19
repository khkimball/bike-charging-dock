import math

from build123d import Axis

from dock import deck, divider, params


def test_deck_fits_bed():
    assert deck.DECK_X <= params.BED_X
    assert deck.DECK_Y <= params.BED_Y


def test_deck_valid_and_flat_on_bed():
    p = deck.build_deck()
    assert p.is_valid  # property in build123d 0.12, not a method
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_layout_has_four_stations_without_overlap():
    lay = deck.layout()
    assert set(lay) == {"ion", "roam", "trackr", "spare"}
    xs = sorted(v[0] for v in lay.values())
    assert all(b - a > 20 for a, b in zip(xs, xs[1:]))


def test_deck_has_at_least_four_floor_slots():
    p = deck.build_deck()
    bottom = p.faces().sort_by(Axis.Z)[0]
    assert len(bottom.inner_wires()) >= 4


def test_plate_is_solid_on_bed():
    """One face spans the whole footprint: the plate lies flat on the bed."""
    p = deck.build_deck()
    bottom = p.faces().sort_by(Axis.Z)[0]
    assert abs(bottom.center().Z) < 1e-6
    size = bottom.outer_wire().bounding_box().size
    assert abs(size.X - deck.DECK_X) < 1e-6
    assert abs(size.Y - deck.DECK_Y) < 1e-6


def test_floor_slots_are_plug_sized():
    """Each slot through the plate is its own plug + CLR_DEVICE per side."""
    p = deck.build_deck()
    bottom = p.faces().sort_by(Axis.Z)[0]
    widths = sorted(round(w.bounding_box().size.X, 3)
                    for w in bottom.inner_wires())
    expect = sorted(round(plug.width + 2 * params.CLR_DEVICE, 3)
                    for plug, _ in deck._PLUGS.values())
    assert widths == expect


def test_plate_is_thick_enough_to_hold_a_plug():
    """The plate bore is the plug well, so it must be a real grip length."""
    assert deck.PLATE_T >= 4 * params.FLOOR


def test_spare_bay_metadata_matches_the_layout():
    x, y, w, l, h = deck.SPARE_BAY
    assert (x, y) == deck.layout()["spare"]
    assert (w, l, h) == (deck.SPARE_W, deck.SPARE_L, deck.SPARE_H)


def test_spare_bay_long_walls_keep_a_wall_behind_each_rail_slot():
    x_rail = deck.SPARE_W / 2 + (divider.RAIL_D + params.CLR_RAIL) / 2
    slot_outer = x_rail + (divider.RAIL_D + params.CLR_RAIL) / 2
    wall_outer = deck.SPARE_W / 2 + deck.SPARE_WALL_X
    assert wall_outer - slot_outer >= params.WALL - 1e-9


def test_no_face_overhangs_past_45_degrees():
    """Bar the bed face, every downward face is <= 45 deg from vertical."""
    p = deck.build_deck()
    for f in p.faces():
        n = f.normal_at(f.center())
        if n.Z < -1e-6 and f.center().Z > 1e-6:
            overhang = math.degrees(math.asin(min(1.0, -n.Z)))
            assert overhang <= 45.0 + 1e-6, f"{overhang:.1f} deg overhang"
