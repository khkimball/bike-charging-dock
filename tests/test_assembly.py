from build123d import Axis

from dock import base, deck, params


def test_plate_fits_rebate_with_clearance():
    assert base.BASE_X - 2 * params.WALL >= deck.DECK_X + 2 * params.CLR_FIT - 1e-6
    assert base.BASE_Y - 2 * params.WALL >= deck.DECK_Y + 2 * params.CLR_FIT - 1e-6


def test_assembled_parts_do_not_intersect():
    d = deck.build_deck()
    b = base.build_base()
    seated = base.deck_seat() * d
    inter = seated & b
    assert inter.volume < 1e-3


def test_plate_top_is_flush_with_base_top():
    assert abs((base.BASE_H - base.REBATE_D + deck.PLATE_T) - base.BASE_H) < 1e-6


def test_seated_deck_top_is_flush_with_base_top_measured():
    """Measured on the solids: the seated deck's flat plate-top face (not
    the taller cradle tops) sits at the same Z as the base's rim top."""
    d = deck.build_deck()
    b = base.build_base()
    plate_top_face = min(
        (f for f in d.faces().filter_by(Axis.Z) if f.normal_at().Z > 0),
        key=lambda f: f.center().Z,
    )
    assert abs(plate_top_face.center().Z - deck.PLATE_T) < 1e-6

    seated_face = base.deck_seat() * plate_top_face
    base_top_z = b.bounding_box().max.Z
    assert abs(seated_face.center().Z - base_top_z) < 1e-6
    assert abs(base_top_z - base.BASE_H) < 1e-6


def test_assembled_footprint_within_bed():
    assert base.BASE_X <= params.BED_X and base.BASE_Y <= params.BED_Y
