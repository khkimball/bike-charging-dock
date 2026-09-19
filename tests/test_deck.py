import math

from dock import deck, divider, params


def _bed_faces(part):
    """The faces lying on the print bed (Z = 0)."""
    return [f for f in part.faces() if abs(f.center().Z) < 1e-6]


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
    """Every station's plug slot runs clear through the plate and its well."""
    p = deck.build_deck()
    slots = sum(len(f.inner_wires()) for f in _bed_faces(p))
    assert slots >= 4


def test_four_plug_wells_stand_on_the_bed():
    """Four well bottoms, each pierced by exactly one slot, all at Z = 0."""
    p = deck.build_deck()
    bed = _bed_faces(p)
    assert len(bed) == 4, f"expected 4 well bottoms on the bed, got {len(bed)}"
    for f in bed:
        assert len(f.inner_wires()) == 1


def test_well_depth_holds_the_longest_plug():
    longest = max(plug.length for plug in (params.USB_A_PLUG,
                                           params.USB_C_PLUG,
                                           params.MICRO_PLUG))
    assert deck.WELL_H >= longest


def test_wells_are_wall_thick_around_each_plug():
    """A well bottom's outer outline is the slot + WALL on every side."""
    p = deck.build_deck()
    for f in _bed_faces(p):
        outer = f.outer_wire().bounding_box().size
        inner = f.inner_wires()[0].bounding_box().size
        assert outer.X - inner.X >= 2 * params.WALL - 1e-6
        assert outer.Y - inner.Y >= 2 * params.WALL - 1e-6


def test_lip_hangs_below_the_plate_and_is_inset():
    p = deck.build_deck()
    z = deck.WELL_H - deck.LIP_H
    ring = [f for f in p.faces() if abs(f.center().Z - z) < 1e-6]
    assert len(ring) == 1, "expected one rectangular lip bottom face"
    assert len(ring[0].inner_wires()) == 1, "lip must be a skirt, not a slab"
    size = ring[0].bounding_box().size
    inset = 2 * (params.WALL + params.CLR_FIT)
    assert abs(size.X - (deck.DECK_X - inset)) < 1e-6
    assert abs(size.Y - (deck.DECK_Y - inset)) < 1e-6


def test_spare_bay_metadata_matches_the_layout():
    x, y, w, l, h = deck.SPARE_BAY
    assert (x, y) == deck.layout()["spare"]
    assert (w, l, h) == (deck.SPARE_W, deck.SPARE_L, deck.SPARE_H)


def test_divider_rails_stay_inside_the_spare_bay_walls():
    """Rail slots must not cut through the outside of the bay's long walls."""
    x_rail = deck.SPARE_W / 2 + (divider.RAIL_D + params.CLR_RAIL) / 2
    outer = x_rail + (divider.RAIL_D + params.CLR_RAIL) / 2
    assert outer <= deck.SPARE_W / 2 + params.WALL + 1e-9


def test_no_sloped_face_overhangs_past_45_degrees():
    """Every sloping downward face (chamfers, the leaning Roam well) is <= 45
    deg from vertical.  Horizontal downward faces are excluded: the plate
    underside and the lip/well bottoms are flat by design, not slopes."""
    p = deck.build_deck()
    for f in p.faces():
        n = f.normal_at(f.center())
        if n.Z < -1e-6 and abs(n.Z + 1.0) > 1e-6:
            overhang = math.degrees(math.asin(min(1.0, -n.Z)))
            assert overhang <= 45.0 + 1e-6, f"{overhang:.1f} deg overhang"
