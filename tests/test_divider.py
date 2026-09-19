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
