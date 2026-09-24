"""Hinge pieces measured on their own; the swing is in test_assembly."""
import math

from build123d import Align, Box, Pos, Rot

from dock import hinge as H, layout as L
from printability import span, steep_faces

MAX_BRIDGE = 20.0


def _along_axis(x0, x1, r):
    return H.x_cylinder(r, x0, x1)


def test_hull2d_drops_interior_points():
    pts = [(0, 0), (2, 0), (2, 2), (0, 2), (1, 1)]
    assert sorted(H.hull2d(pts)) == [(0, 0), (0, 2), (2, 0), (2, 2)]


def test_two_stations_each_one_solid():
    assert len(H.base_knuckles().solids()) == 2
    assert len(H.lid_hooks().solids()) == 2


def test_the_pin_sits_in_the_bore_with_clearance():
    assert (H.base_knuckles() & H.lid_hooks()).volume < 1e-6


def test_the_bore_is_clear_to_its_radius():
    for xs in H.STATIONS:
        x0, x1 = xs - H.HOOK_W / 2, xs + H.HOOK_W / 2
        hooks = H.lid_hooks()
        assert (_along_axis(x0, x1, H.BORE_R - 0.02) & hooks).volume < 1e-6
        assert (_along_axis(x0, x1, H.BORE_R + 0.1) & hooks).volume > 1e-3


def _mouth_probe(xs, width):
    """A bar from the axis out along the mouth, `width` across."""
    a = H.MOUTH_DEG
    bar = Box(H.HOOK_W, H.KNUCKLE_R + 2.0, width, align=(Align.CENTER, Align.MIN, Align.CENTER))
    return Pos(xs, H.AXIS_Y, H.AXIS_Z) * Rot(a, 0, 0) * bar


def test_the_mouth_neck_is_narrower_than_the_pin_by_the_snap():
    hooks = H.lid_hooks()
    for xs in H.STATIONS:
        assert (_mouth_probe(xs, H.MOUTH_W - 0.02) & hooks).volume < 1e-6
        assert (_mouth_probe(xs, H.MOUTH_W + 0.1) & hooks).volume > 1e-4
    assert H.MOUTH_W < 2 * H.PIN_R


def test_the_pin_underside_bridges_the_hook_gap_and_the_cheeks_print_unsupported():
    steep = steep_faces(H.base_knuckles())
    assert steep, "expected the pins' flat undersides"
    for f in steep:
        assert span(f) <= H.HOOK_W + 2 * H.SIDE_CLR + 1.0 + 1e-6
        assert math.isclose(f.center().Z, H.AXIS_Z - H.PIN_FLAT * H.PIN_R, abs_tol=1e-6)


def test_the_mouth_faces_straight_down_with_the_lid_closed():
    hooks = H.lid_hooks()
    xs = H.STATIONS[0]
    below = Pos(xs, H.AXIS_Y, H.AXIS_Z - H.KNUCKLE_R) * Box(H.HOOK_W - 2, H.MOUTH_W - 0.2, 2 * H.KNUCKLE_R - 2 * H.BORE_R,
                                                           align=(Align.CENTER, Align.CENTER, Align.MIN))
    assert (below & hooks).volume < 1e-6
    above = Pos(xs, H.AXIS_Y, H.AXIS_Z + H.BORE_R + 0.2) * Box(H.HOOK_W - 2, H.MOUTH_W - 0.2, 1.0,
                                                              align=(Align.CENTER, Align.CENTER, Align.MIN))
    assert (above & hooks).volume > 1e-3


def test_the_axis_is_behind_the_rim_and_the_knuckle_sweep_clears_the_tray():
    assert H.AXIS_Y > L.RIM.sy / 2
    assert H.AXIS_Y - H.RELIEF_R > L.TRAY_OUTLINE.sy / 2


def test_opened_turns_the_lid_up_and_back():
    y, z = H.AXIS_Y - 10.0, H.AXIS_Z          # a point on the lid, 10 mm in front of the axis
    p = H.opened(90.0) * Pos(0, y, z)
    assert math.isclose(p.position.Y, H.AXIS_Y, abs_tol=1e-6)
    assert math.isclose(p.position.Z, H.AXIS_Z + 10.0, abs_tol=1e-6)
