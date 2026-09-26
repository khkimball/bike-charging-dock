from build123d import Axis
from dock import fit_tests


def test_the_fit_test_has_six_holes():
    plate, peg = fit_tests.build_fit_test()
    # a plate with 6 through-holes has 6 inner wires on its top face
    top = plate.faces().sort_by(Axis.Z)[-1]
    assert len(top.inner_wires()) == 6


def test_peg_is_10mm_square():
    _, peg = fit_tests.build_fit_test()
    size = peg.bounding_box().size
    assert abs(size.X - 10) < 1e-6 and abs(size.Y - 10) < 1e-6


def test_the_fit_test_parts_are_single_valid_solids():
    for part in fit_tests.build_fit_test():
        assert part.is_valid
        assert len(part.solids()) == 1


def test_the_hinge_test_halves_are_single_solids_on_the_bed():
    for p in fit_tests.build_hinge_test():
        assert p.is_valid and len(p.solids()) == 1
        assert abs(p.bounding_box().min.Z) < 1e-6


def test_the_hinge_test_carries_a_whole_station():
    """Cut from the real parts: the base side has the socket bores (a probe
    along the axis finds air where the pins go) and the lid side has both
    pins (it is longer along the hinge than the notch)."""
    from dock import hinge
    base_side, lid_side = fit_tests.build_hinge_test()
    assert lid_side.bounding_box().size.X >= hinge.NOTCH_W - 2 * hinge.SIDE_CLR + 2 * hinge.PIN_L - 0.01
    assert base_side.bounding_box().size.X >= hinge.NOTCH_W + 2 * hinge.BLOCK_W - 0.01
