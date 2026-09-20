from build123d import Axis

from dock import divider, params


def test_divider_bounding_box():
    p = divider.build_divider(height=40, width=50)
    s = p.bounding_box().size
    assert abs(s.Z - 40) < 1e-6
    assert abs(s.X - (50 + 2 * divider.RAIL_D)) < 1e-6
    assert abs(s.Y - divider.RAIL_W) < 1e-6


def test_cutter_is_larger_than_rail_by_clearance():
    cut = divider.rail_cutter(height=40).bounding_box().size
    assert abs(cut.Y - (divider.RAIL_W + 2 * params.CLR_RAIL)) < 1e-6
    assert abs(cut.X - (divider.RAIL_D + params.CLR_RAIL)) < 1e-6


def test_bottom_edge_is_chamfered_not_filleted():
    """The divider prints standing on its bottom edge, so that edge is a
    downward edge: the bed face is inset by the chamfer all round while the
    part keeps its full size above it."""
    c = 0.5
    p = divider.build_divider(height=40, width=50, bottom_chamfer=c)
    bb = p.bounding_box().size
    bed = p.faces().sort_by(Axis.Z)[0].bounding_box().size
    assert abs(bed.X - (bb.X - 2 * c)) < 1e-6
    assert abs(bed.Y - (bb.Y - 2 * c)) < 1e-6


def test_the_chamfer_can_be_switched_off():
    p = divider.build_divider(height=40, width=50, bottom_chamfer=0)
    bb = p.bounding_box().size
    bed = p.faces().sort_by(Axis.Z)[0].bounding_box().size
    assert abs(bed.X - bb.X) < 1e-6 and abs(bed.Y - bb.Y) < 1e-6
