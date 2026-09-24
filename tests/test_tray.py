"""Tray tests: measured on the built solid."""
import math
from functools import lru_cache

from build123d import Align, Axis, Box, Pos

from dock import layout as L, params, taper, tray
from printability import steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@lru_cache(maxsize=None)
def _tray():
    return tray.build_tray()


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=_CTR)


def _solid(probe):
    return (probe & _tray()).volume >= probe.volume * (1 - 1e-4)


def _clear(probe):
    return (probe & _tray()).volume < probe.volume * 1e-6


def _slab(z):
    return _tray() & (Pos(0, 0, z) * Box(400, 400, 2e-3, align=_CTR))


def test_tray_is_one_valid_solid_on_the_bed_and_fits_it():
    p = _tray()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6 and bb.size.X <= params.BED_X and bb.size.Y <= params.BED_Y


def test_the_outer_walls_lean_at_the_draft_up_to_the_layout_outline():
    z0, z1 = 10.0, 35.0
    lean = (_slab(z0).bounding_box().min.Y - _slab(z1).bounding_box().min.Y) / (z1 - z0)
    assert math.isclose(lean, taper.TAN, abs_tol=1e-3)
    bb = _slab(L.TRAY_H - 0.01).bounding_box()
    assert math.isclose(bb.size.X, L.TRAY_OUTLINE.at(L.TRAY_H - 0.01)[0], abs_tol=0.02)


def test_the_outer_wall_is_thin_wall_thick_square_to_the_slope():
    b = L.BAYS["roam"]
    z = 20.0
    y_out = -L.TRAY_OUTLINE.at(z)[1] / 2
    w = tray.WALL_H
    assert _solid(_box(b.cx, y_out + w / 2, z, 4, w - 0.1, 0.02))
    assert _clear(_box(b.cx, y_out + w + 0.1, z, 4, 0.1, 0.02))


def test_the_plate_is_tray_plate_thick():
    b = L.BAYS["trackr"]
    x = b.x0 + 20.0
    assert _solid(_box(x, b.cy, params.TRAY_PLATE / 2, 2, 2, params.TRAY_PLATE - 0.04))
    assert _clear(_box(x, b.cy, params.TRAY_PLATE + 5.0, 2, 2, 5.0))


def test_every_device_lies_in_its_bay_clear_of_the_tray():
    for name, dev in L.DEVICES.items():
        x0, x1, y0, y1 = L.device_footprint(name)
        box = Pos((x0 + x1) / 2, (y0 + y1) / 2, params.TRAY_PLATE + 0.01) * Box(
            x1 - x0, y1 - y0, dev.thickness, align=_MIN)
        assert _clear(box), name


def test_the_bays_are_open_to_the_rim():
    for b in L.BAYS.values():
        assert _clear(_box(b.cx, b.cy, (L.TRAY_H + params.TRAY_PLATE) / 2 + 3, 10, 10, L.TRAY_H - params.TRAY_PLATE - 6))


def test_the_internal_walls_are_fixed_and_wall_thick():
    part_x = tray.PARTITION_X
    assert _solid(_box(part_x, 40.0, 25.0, params.WALL - 0.05, 5, 5))
    for y0, y1 in ((L.BAYS["spare"].y1, L.BAYS["trackr"].y0), (L.BAYS["trackr"].y1, L.BAYS["ion"].y0)):
        assert math.isclose(y1 - y0, params.WALL)
        assert _solid(_box(L.BAYS["trackr"].cx, (y0 + y1) / 2, 25.0, 20, params.WALL - 0.05, 5))


def test_inside_corners_are_filleted_about_r6():
    # where the spare/trackr divider meets the partition, on the trackr side
    x = L.BAYS["trackr"].x0
    y = L.BAYS["trackr"].y0
    r = L.INNER_FILLET_R
    assert _solid(_box(x + 0.25 * r, y + 0.25 * r, 20.0, 0.1, 0.1, 0.1))
    assert _clear(_box(x + 0.35 * r, y + 0.35 * r, 20.0, 0.1, 0.1, 0.1))


def test_walls_meet_the_floor_in_an_r3_fillet():
    x = L.BAYS["trackr"].x0            # the partition's +X face
    y = L.BAYS["trackr"].cy
    r = L.FLOOR_FILLET_R
    z = params.TRAY_PLATE
    assert _solid(_box(x + 0.25 * r, y, z + 0.25 * r, 0.1, 0.1, 0.1))
    assert _clear(_box(x + 0.35 * r, y, z + 0.35 * r, 0.1, 0.1, 0.1))


def test_the_internal_wall_tops_are_rounded():
    x = tray.PARTITION_X + params.WALL / 2 - 0.1
    assert _clear(_box(x, 40.0, L.TRAY_H - 0.1, 0.1, 1, 0.1))
    assert _solid(_box(tray.PARTITION_X, 40.0, L.TRAY_H - 0.1, 0.1, 1, 0.1))


def test_one_cable_cutout_per_bay_through_the_plate_where_the_layout_puts_it():
    bottom = _tray().faces().sort_by(Axis.Z)[0]
    holes = sorted((w.bounding_box().center().X, w.bounding_box().center().Y) for w in bottom.inner_wires())
    want = sorted((c[1], c[2]) for c in L.cutouts())
    assert len(holes) == len(want) == len(L.BAYS)
    for (hx, hy), (wx, wy) in zip(holes, want):
        assert math.isclose(hx, wx, abs_tol=0.01) and math.isclose(hy, wy, abs_tol=0.01)


def test_the_cable_cutouts_are_ovals():
    for _, cx, cy, sx, sy in L.cutouts():
        long_x = sx >= sy
        length, width = (sx, sy) if long_x else (sy, sx)
        z = params.TRAY_PLATE / 2
        # the straight middle is open the full width
        mid = _box(cx, cy, z, *(((length - width), width - 0.1) if long_x
                                else (width - 0.1, (length - width))), 0.2)
        assert _clear(mid)
        # but the corner of the bounding rectangle is plate: the ends are round
        ex = cx + (length / 2 - 0.3 if long_x else width / 2 - 0.3)
        ey = cy + (width / 2 - 0.3 if long_x else length / 2 - 0.3)
        assert _solid(_box(ex, ey, z, 0.2, 0.2, 0.2))


def test_the_partition_is_unbroken():
    """No finger slot: the tray lifts out by its walls, so the partition is
    solid full height and full length."""
    y0, y1 = -L.FLOOR_Y / 2 + 8.0, L.FLOOR_Y / 2 - 8.0
    z0, z1 = params.TRAY_PLATE + 4.0, L.TRAY_H - 2.0
    assert _solid(_box(tray.PARTITION_X, (y0 + y1) / 2, (z0 + z1) / 2,
                       params.WALL - 0.2, y1 - y0, z1 - z0))


def test_the_tray_prints_with_no_overhang():
    assert steep_faces(_tray()) == []
