from build123d import Axis
from dock import tray, params, divider
from dock import measurements as m


def test_tray_fits_bed():
    s = tray.build_tray().bounding_box().size
    assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_tray_is_one_valid_solid_on_bed():
    p = tray.build_tray()
    assert p.is_valid and len(p.solids()) == 1
    assert abs(p.bounding_box().min.Z) < 1e-6
    assert abs(p.bounding_box().size.Z - tray.TRAY_H) < 1e-6


def test_four_cable_cutouts_through_the_plate():
    p = tray.build_tray()
    bottom = p.faces().sort_by(Axis.Z)[0]
    wires = bottom.inner_wires()
    assert len(wires) == 4
    for w in wires:
        s = w.bounding_box().size
        assert {round(s.X, 3), round(s.Y, 3)} == {tray.CUTOUT[0], tray.CUTOUT[1]}


def test_each_device_fits_its_bay_with_clearance():
    for dev, (x0, y0, w, l) in ((m.ROAM, tray.ROAM_BAY),):
        assert w >= dev.width + 2 * params.CLR_BAY - 1e-6
        assert l >= dev.length + 2 * params.CLR_BAY + tray.CUTOUT[0] - 1e-6
    for name, dev in (("ion", m.ION), ("trackr", m.TRACKR)):
        x0, y0, w, l = tray.RIGHT_BAYS[name]
        assert w >= dev.length + 2 * params.CLR_BAY + tray.CUTOUT[0] - 1e-6
        assert l >= dev.width + 2 * params.CLR_BAY - 1e-6


def test_bays_are_open_voids_of_full_depth():
    """A box the size of each bay interior, sitting on the plate, does not intersect the tray."""
    from build123d import Box, Pos, Align
    p = tray.build_tray()
    bays = [tray.ROAM_BAY, *tray.RIGHT_BAYS.values()]
    for (x0, y0, w, l) in bays:
        probe = Pos(x0 + w / 2, y0 + l / 2, params.TRAY_PLATE) * Box(w - 0.01, l - 0.01, params.BAY_DEPTH - 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (probe & p).volume < 1e-3


def test_divider_drops_into_both_rail_positions():
    from build123d import Pos
    p = tray.build_tray()
    d = divider.build_divider(height=params.BAY_DEPTH, width=tray.RIGHT_BAY_W - params.CLR_RAIL)
    for y in tray.RAIL_YS:
        placed = Pos(tray.RIGHT_BAYS["ion"][0] + tray.RIGHT_BAY_W / 2, y, params.TRAY_PLATE) * d
        assert (placed & p).volume < 1e-3


def test_walls_keep_full_thickness_behind_rail_slots():
    """Probe the material behind each rail slot: at least WALL remains."""
    from build123d import Box, Pos, Align
    p = tray.build_tray()
    x_part = tray.RIGHT_BAYS["ion"][0]          # partition's +X face
    for y in tray.RAIL_YS:
        probe = Pos(x_part - divider.RAIL_D - params.CLR_RAIL - params.WALL / 2, y, params.TRAY_PLATE + 1) * Box(params.WALL - 0.02, 2, params.BAY_DEPTH - 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert abs((probe & p).volume - probe.volume) < 1e-3


def test_outer_corners_are_rounded():
    from build123d import GeomType
    p = tray.build_tray()
    cyl = [f for f in p.faces() if f.geom_type == GeomType.CYLINDER and abs(f.radius - tray.OUTER_R) < 1e-6]
    assert len(cyl) >= 4


def test_no_overhang_past_45_degrees():
    import math
    p = tray.build_tray()
    for f in p.faces():
        n = f.normal_at()
        if n.Z < -1e-6 and f.center().Z > 1e-6:
            angle = math.degrees(math.acos(-n.Z))   # 0 = flat ceiling
            assert angle >= 45 - 1e-6 or f.bounding_box().size.length <= 20, f.center()
