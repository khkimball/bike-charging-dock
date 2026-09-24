"""The layout is numbers, so these check the relations the parts rely on:
bays tile the tray floor, devices fit their bays, the stack-up adds up."""
import math

from dock import measurements as m
from dock import layout as L, params, taper


def test_the_four_bays_tile_the_tray_floor_with_wall_thick_gaps():
    b = L.BAYS
    assert math.isclose(b["spare"].x0 - b["roam"].x1, params.WALL)
    assert math.isclose(b["trackr"].y0 - b["spare"].y1, params.WALL)
    assert math.isclose(b["ion"].y0 - b["trackr"].y1, params.WALL)
    assert math.isclose(b["roam"].x0, -L.FLOOR_X / 2)
    assert math.isclose(b["spare"].x1, L.FLOOR_X / 2)
    for bay in b.values():
        assert bay.y0 >= -L.FLOOR_Y / 2 - 1e-9 and bay.y1 <= L.FLOOR_Y / 2 + 1e-9


def test_a_bay_side_is_sloped_exactly_when_it_is_on_the_floor_outline():
    for bay in L.BAYS.values():
        on_edge = (math.isclose(bay.x0, -L.FLOOR_X / 2), math.isclose(bay.x1, L.FLOOR_X / 2),
                   math.isclose(bay.y0, -L.FLOOR_Y / 2), math.isclose(bay.y1, L.FLOOR_Y / 2))
        assert bay.sloped == on_edge, bay.name


def test_each_device_sits_inside_its_bay_with_its_clearances():
    for name in L.DEVICES:
        bay = L.BAYS[name]
        x0, x1, y0, y1 = L.device_footprint(name)
        sides = (x0 - bay.x0, bay.x1 - x1, y0 - bay.y0, bay.y1 - y1)
        for i, (gap, sloped) in enumerate(zip(sides, bay.sloped)):
            need = params.CLR_BAY_OUTER if sloped else params.CLR_BAY
            if name == "ion" and i == 2:        # moved forward, clear of the hinge recess
                need -= L.HEADLIGHT_FORWARD
            assert gap >= need - 1e-9, (name, gap, need)


def test_cutouts_sit_in_their_bays_clear_of_the_floor_fillet_and_the_device():
    for name, cx, cy, sx, sy in L.cutouts():
        bay = L.BAYS[name]
        assert bay.x0 + L.FLOOR_FILLET_R < cx - sx / 2 and cx + sx / 2 < bay.x1 - L.FLOOR_FILLET_R
        assert bay.y0 + L.FLOOR_FILLET_R < cy - sy / 2 and cy + sy / 2 < bay.y1 - L.FLOOR_FILLET_R
        if name in L.DEVICES:
            x0, x1, y0, y1 = L.device_footprint(name)
            clear_x = cx + sx / 2 <= x0 or cx - sx / 2 >= x1
            clear_y = cy + sy / 2 <= y0 or cy - sy / 2 >= y1
            assert clear_x or clear_y, name


def test_one_cutout_per_bay():
    names = [c[0] for c in L.cutouts()]
    assert sorted(names) == sorted(L.BAYS)


def test_the_stack_up_puts_the_tray_on_the_cable_room_above_the_charger():
    assert math.isclose(L.TRAY_Z0, params.FLOOR + m.CHARGER.height + L.CABLE_ROOM)
    assert math.isclose(L.TRAY_Z0 + L.TRAY_H + L.TRAY_SINK, L.BASE_H)


def test_the_tray_and_the_rim_share_corner_centres():
    t, r = L.TRAY_OUTLINE, L.RIM
    at_rim = t.at(L.TRAY_H + L.TRAY_SINK)   # the tray outline carried up to rim height
    assert math.isclose(r.sx / 2 - r.r, at_rim[0] / 2 - at_rim[2], abs_tol=1e-9)


def test_the_tray_floor_outline_is_the_bays_plus_a_thin_wall():
    sx, sy, _ = L.TRAY_OUTLINE.at(params.TRAY_PLATE)
    assert math.isclose(sx, L.FLOOR_X + 2 * taper.horiz(params.THIN_WALL))
    assert math.isclose(sy, L.FLOOR_Y + 2 * taper.horiz(params.THIN_WALL))


def test_the_lid_lip_keeps_at_least_a_millimetre_inside_the_bed():
    assert 1.0 <= L.LIP_W <= L.LIP_W_MAX
