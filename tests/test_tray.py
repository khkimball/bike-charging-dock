import math

from build123d import Align, Axis, Box, GeomType, Pos, Rot, fillet

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


def _expected_cutout_count():
    return 1 + sum(tray.UNDERSIDE_PORT_CUTOUTS.get(n, 1) for n in tray.RIGHT_BAYS)


def test_cable_cutouts_through_the_plate():
    p = tray.build_tray()
    bottom = p.faces().sort_by(Axis.Z)[0]
    wires = bottom.inner_wires()
    assert len(wires) == _expected_cutout_count()
    for w in wires:
        s = w.bounding_box().size
        assert {round(s.X, 3), round(s.Y, 3)} == {tray.CUTOUT[0], tray.CUTOUT[1]}


def test_each_device_fits_its_bay_with_clearance():
    # The ROAM lies along Y, so its length runs down the bay and the cutout
    # is reserved at the bay's -Y end.
    _, _, w, l = tray.ROAM_BAY
    assert w >= m.ROAM.width + 2 * params.CLR_BAY - 1e-6
    assert l >= m.ROAM.length + 2 * params.CLR_BAY + tray.CUTOUT[0] - 1e-6
    # The right column runs along X, with the cutout at each bay's +X end.
    for name, dev in (("ion", m.ION), ("trackr", m.TRACKR)):
        _, _, w, l = tray.RIGHT_BAYS[name]
        assert w >= dev.length + 2 * params.CLR_BAY + tray.CUTOUT[0] - 1e-6, name
        assert l >= dev.width + 2 * params.CLR_BAY - 1e-6, name


def test_bays_are_open_voids_of_full_depth():
    """A box the size of each bay interior, sitting on the plate, does not
    intersect the tray.  The ROAM bay's -X corners are rounded (they stand
    behind the tray's own outer corners), so its probe is rounded to match."""
    p = tray.build_tray()
    bays = [(tray.ROAM_BAY, True), *((b, False) for b in tray.RIGHT_BAYS.values())]
    for (x0, y0, w, l), round_min_x in bays:
        box = Box(w - 0.01, l - 0.01, params.BAY_DEPTH - 0.01,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
        if round_min_x:
            box = fillet(box.edges().filter_by(Axis.Z).group_by(Axis.X)[0],
                         tray.BAY_CORNER_R)
        probe = Pos(x0 + w / 2, y0 + l / 2, params.TRAY_PLATE) * box
        assert (probe & p).volume < 1e-3, (x0, y0)


def test_the_roam_still_fits_its_bay_between_the_rounded_corners():
    """Rounding the ROAM bay's -X corners must not eat into the device room:
    a ROAM-sized block, inset CLR_BAY from the walls and pushed to the +Y end
    away from its cable cutout, still touches nothing."""
    p = tray.build_tray()
    x0, y0, w, l = tray.ROAM_BAY
    probe = Pos(x0 + params.CLR_BAY,
                y0 + l - params.CLR_BAY - m.ROAM.length,
                params.TRAY_PLATE) * Box(
        m.ROAM.width, m.ROAM.length, m.ROAM.thickness,
        align=(Align.MIN, Align.MIN, Align.MIN))
    assert (probe & p).volume < 1e-3


def test_divider_drops_into_both_rail_positions():
    p = tray.build_tray()
    d = divider.build_divider(height=params.BAY_DEPTH, width=tray.RIGHT_BAY_W - params.CLR_RAIL)
    for y in tray.RAIL_YS:
        placed = Pos(tray.RIGHT_BAYS["ion"][0] + tray.RIGHT_BAY_W / 2, y, params.TRAY_PLATE) * d
        assert (placed & p).volume < 1e-3


def test_walls_keep_full_thickness_behind_rail_slots():
    """Probe the material behind each rail slot, in both slotted walls:
    at least WALL remains between the slot and the outside world."""
    p = tray.build_tray()
    x_part = tray.RIGHT_BAYS["ion"][0]                          # partition's +X face
    x_out = x_part + tray.RIGHT_BAY_W                           # +X outer wall's -X face
    back = divider.RAIL_D + params.CLR_RAIL + params.WALL / 2   # slot depth + half the remnant
    for y in tray.RAIL_YS:
        for x in (x_part - back, x_out + back):
            probe = Pos(x, y, params.TRAY_PLATE + 1) * Box(params.WALL - 0.02, 2, params.BAY_DEPTH - 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            assert abs((probe & p).volume - probe.volume) < 1e-3, (x, y)


def test_outer_corners_are_rounded():
    p = tray.build_tray()
    cyl = [f for f in p.faces() if f.geom_type == GeomType.CYLINDER and abs(f.radius - tray.OUTER_R) < 1e-6]
    assert len(cyl) >= 4


def test_no_overhang_past_45_degrees():
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
    """The cable-cutout wires in the plate's bottom face, split into the one
    running along Y (the left bay's) and those running along X (right bays)."""
    wires = p.faces().sort_by(Axis.Z)[0].inner_wires()
    along_y = [w for w in wires if w.bounding_box().size.Y > w.bounding_box().size.X]
    along_x = [w for w in wires if w.bounding_box().size.X > w.bounding_box().size.Y]
    return along_y, along_x


def test_left_cutout_sits_at_the_near_end_centred_in_its_bay():
    p = tray.build_tray()
    along_y, along_x = _bottom_cutout_wires(p)
    assert len(along_y) == 1 and len(along_x) == _expected_cutout_count() - 1
    b = along_y[0].bounding_box()
    assert abs(b.min.Y - (-tray.TRAY_Y / 2 + params.WALL + tray.CUTOUT_INSET)) < 1e-6
    x0, _, w, _ = tray.ROAM_BAY
    assert abs(b.center().X - (x0 + w / 2)) < 1e-6


def _wires_in_bay(along_x, name):
    _, y0, _, l = tray.RIGHT_BAYS[name]
    return [w for w in along_x if abs(w.bounding_box().center().Y - (y0 + l / 2)) < 1e-6]


def test_single_cutout_bays_have_it_at_the_far_end():
    p = tray.build_tray()
    _, along_x = _bottom_cutout_wires(p)
    far = tray.TRAY_X - tray.RAIL_WALL - tray.CUTOUT_INSET
    for name in tray.RIGHT_BAYS:
        if tray.UNDERSIDE_PORT_CUTOUTS.get(name, 1) != 1:
            continue
        ws = _wires_in_bay(along_x, name)
        assert len(ws) == 1, name
        assert abs(ws[0].bounding_box().max.X - far) < 1e-6, name


def test_underside_port_bay_has_evenly_spaced_cutouts_along_it():
    """The Ion charges from its underside: three cutouts, one centred in each
    third of the bay, all inside the bay footprint and clear of the walls."""
    p = tray.build_tray()
    _, along_x = _bottom_cutout_wires(p)
    for name, n in tray.UNDERSIDE_PORT_CUTOUTS.items():
        x0, y0, w, l = tray.RIGHT_BAYS[name]
        ws = sorted(_wires_in_bay(along_x, name), key=lambda w: w.bounding_box().center().X)
        assert len(ws) == n, name
        xs = [w.bounding_box().center().X for w in ws]
        section = w / n
        for i, x in enumerate(xs):
            assert abs(x - (x0 + section * (i + 0.5))) < 1e-6, (name, i)
        gaps = [b - a for a, b in zip(xs, xs[1:])]
        assert all(abs(g - gaps[0]) < 1e-6 for g in gaps)
        for wire in ws:
            b = wire.bounding_box()
            assert b.min.X > x0 + 1.0 and b.max.X < x0 + w - 1.0
            assert b.min.Y > y0 + 1.0 and b.max.Y < y0 + l - 1.0


def test_declared_outer_size_matches_the_built_solid():
    s = tray.build_tray().bounding_box().size
    assert abs(s.X - tray.TRAY_X) < 1e-6
    assert abs(s.Y - tray.TRAY_Y) < 1e-6


def test_partition_and_outer_wall_are_rail_wall_thick():
    """Both slotted walls are solid RAIL_WALL thick away from the slots, and
    no thicker: the bay faces either side of the probe are void."""
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


# --- outer corner walls -------------------------------------------------------

# Where the four outer corner arcs are centred, and the outward 45 degree
# diagonal at each: the thinnest line through a corner.
_X_LO, _X_HI = tray.OUTER_R, tray.TRAY_X - tray.OUTER_R
_Y_LO, _Y_HI = -tray.TRAY_Y / 2 + tray.OUTER_R, tray.TRAY_Y / 2 - tray.OUTER_R
_CORNERS = [
    (_X_LO, _Y_LO, 225),
    (_X_LO, _Y_HI, 135),
    (_X_HI, _Y_LO, 315),
    (_X_HI, _Y_HI, 45),
]


def _corner_probe(cx, cy, angle, length, width=0.2):
    """A thin bar lying along the corner's outward diagonal, from just inside
    the outer surface and `length` deep into the wall."""
    mid = tray.OUTER_R - 0.02 - length / 2
    return (Pos(cx + mid * math.cos(math.radians(angle)),
                cy + mid * math.sin(math.radians(angle)),
                params.TRAY_PLATE + 2)
            * Rot(0, 0, angle)
            * Box(length, width, params.BAY_DEPTH - 6,
                  align=(Align.CENTER, Align.CENTER, Align.MIN)))


def test_outer_corner_walls_are_at_least_wall_thick():
    """The diagonal through a corner is the shortest line from the outside
    world to the bay void, so a square-cornered bay void behind a rounded
    outer corner thins the shell there.  Measured on the solid: at every
    corner, WALL of material stands on that diagonal."""
    p = tray.build_tray()
    assert len(_CORNERS) == 4
    for cx, cy, angle in _CORNERS:
        probe = _corner_probe(cx, cy, angle, params.WALL - 0.05)
        assert abs((probe & p).volume - probe.volume) < 1e-3, (cx, cy, angle)
