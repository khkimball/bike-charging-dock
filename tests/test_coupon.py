from build123d import Axis
from dock import coupon


def test_coupon_has_six_holes():
    plate, peg = coupon.build_coupon()
    # a plate with 6 through-holes has 6 inner wires on its top face
    top = plate.faces().sort_by(Axis.Z)[-1]
    assert len(top.inner_wires()) == 6


def test_peg_is_10mm_square():
    _, peg = coupon.build_coupon()
    size = peg.bounding_box().size
    assert abs(size.X - 10) < 1e-6 and abs(size.Y - 10) < 1e-6


def test_coupon_parts_are_single_valid_solids():
    for part in coupon.build_coupon():
        assert part.is_valid
        assert len(part.solids()) == 1


def test_hinge_coupon_halves_are_single_solids_on_the_bed():
    for p in coupon.build_hinge_coupon():
        assert p.is_valid and len(p.solids()) == 1
        assert abs(p.bounding_box().min.Z) < 1e-6


def test_the_hinge_coupon_prints_like_the_dock_hinge():
    from dock import hinge
    from printability import span, steep_faces
    base_side, lid_side = coupon.build_hinge_coupon()
    flats = steep_faces(base_side)
    assert len(flats) == 1          # the pin's flat underside, and nothing else
    assert span(flats[0]) <= hinge.HOOK_W + 2 * hinge.SIDE_CLR + 1.0
    for f in steep_faces(lid_side):  # only the mouth's short roof
        assert span(f) <= hinge.HOOK_W + 1e-6
