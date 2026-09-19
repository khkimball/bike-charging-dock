from build123d import Axis

from dock import base, deck, params


def _rebate_opening_size(b):
    """XY size of the rebate opening, measured off the ledge face just below
    the base's top rim (the widest point of the rebate cut)."""
    z = base.BASE_H - base.REBATE_D
    ledge = [f for f in b.faces().filter_by(Axis.Z)
             if abs(f.center().Z - z) < 1e-6 and f.normal_at().Z > 0]
    assert ledge, "no horizontal ledge face at the bottom of the rebate"
    bb = ledge[0].bounding_box()
    return bb.size.X, bb.size.Y


def test_plate_fits_rebate_with_clearance():
    """Measured on the solids: the rebate opening is exactly CLR_FIT bigger
    than the built deck's footprint on every side."""
    b = base.build_base()
    d = deck.build_deck()
    open_x, open_y = _rebate_opening_size(b)
    deck_bb = d.bounding_box()
    assert abs((open_x - deck_bb.size.X) / 2 - params.CLR_FIT) < 1e-6
    assert abs((open_y - deck_bb.size.Y) / 2 - params.CLR_FIT) < 1e-6


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
    """Measured on the solid: the built base's bounding box fits the bed."""
    bb = base.build_base().bounding_box()
    assert bb.size.X <= params.BED_X and bb.size.Y <= params.BED_Y
