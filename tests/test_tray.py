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
    """Probe the material behind each rail slot, in both slotted walls:
    at least WALL remains between the slot and the outside world."""
    from build123d import Box, Pos, Align
    p = tray.build_tray()
    x_part = tray.RIGHT_BAYS["ion"][0]                          # partition's +X face
    x_out = x_part + tray.RIGHT_BAY_W                           # +X outer wall's -X face
    back = divider.RAIL_D + params.CLR_RAIL + params.WALL / 2   # slot depth + half the remnant
    for y in tray.RAIL_YS:
        for x in (x_part - back, x_out + back):
            probe = Pos(x, y, params.TRAY_PLATE + 1) * Box(params.WALL - 0.02, 2, params.BAY_DEPTH - 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            assert abs((probe & p).volume - probe.volume) < 1e-3, (x, y)


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


def test_bay_depth_clears_the_tallest_device():
    """Walls must stand proud of every device, so the lid never touches one."""
    tallest = max(d.thickness for d in (m.ROAM, m.ION, m.TRACKR))
    assert params.BAY_DEPTH >= tallest + 1.0


def _bottom_cutout_wires(p):
    """The four cable-cutout wires in the plate's bottom face, split into the
    one running along Y (the left bay's) and the three running along X."""
    wires = p.faces().sort_by(Axis.Z)[0].inner_wires()
    along_y = [w for w in wires if w.bounding_box().size.Y > w.bounding_box().size.X]
    along_x = [w for w in wires if w.bounding_box().size.X > w.bounding_box().size.Y]
    return along_y, along_x


def test_left_cutout_sits_at_the_near_end_centred_in_its_bay():
    p = tray.build_tray()
    along_y, along_x = _bottom_cutout_wires(p)
    assert len(along_y) == 1 and len(along_x) == 3
    b = along_y[0].bounding_box()
    assert abs(b.min.Y - (-tray.TRAY_Y / 2 + params.WALL + tray.CUTOUT_INSET)) < 1e-6
    x0, _, w, _ = tray.ROAM_BAY
    assert abs(b.center().X - (x0 + w / 2)) < 1e-6


def test_right_cutouts_share_the_far_end_and_stack_spare_trackr_ion():
    p = tray.build_tray()
    _, along_x = _bottom_cutout_wires(p)
    far = tray.TRAY_X - tray.RAIL_WALL - tray.CUTOUT_INSET
    for w in along_x:
        assert abs(w.bounding_box().max.X - far) < 1e-6
    ys = sorted(w.bounding_box().center().Y for w in along_x)
    for y, name in zip(ys, ("spare", "trackr", "ion")):
        _, y0, _, l = tray.RIGHT_BAYS[name]
        assert abs(y - (y0 + l / 2)) < 1e-6, name


def test_declared_outer_size_matches_the_built_solid():
    s = tray.build_tray().bounding_box().size
    assert abs(s.X - tray.TRAY_X) < 1e-6
    assert abs(s.Y - tray.TRAY_Y) < 1e-6


def test_partition_and_outer_wall_are_rail_wall_thick():
    """Both slotted walls are solid RAIL_WALL thick away from the slots, and
    no thicker: the bay faces either side of the probe are void."""
    from build123d import Box, Pos, Align
    p = tray.build_tray()
    x_part = tray.RIGHT_BAYS["ion"][0]
    x_out = x_part + tray.RIGHT_BAY_W
    y = 0.0                                   # clear of both RAIL_YS
    assert all(abs(y - ry) > divider.RAIL_W for ry in tray.RAIL_YS)

    def probe(xc, thick):
        return Pos(xc, y, params.TRAY_PLATE + 1) * Box(thick, 2, params.BAY_DEPTH - 2, align=(Align.CENTER, Align.CENTER, Align.MIN))

    for face_x, sign in ((x_part, -1), (x_out, +1)):
        solid = probe(face_x + sign * tray.RAIL_WALL / 2, tray.RAIL_WALL - 0.02)
        assert abs((solid & p).volume - solid.volume) < 1e-3, face_x
        # just past the wall's bay-side face there is nothing
        void = probe(face_x - sign * 0.25, 0.4)
        assert (void & p).volume < 1e-3, face_x
