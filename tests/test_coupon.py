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
