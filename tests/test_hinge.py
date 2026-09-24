"""Hinge pieces measured on their own; the swing, stop and snap are in
test_assembly."""
import math

from build123d import Align, Box, Pos

from dock import hinge as H, layout as L


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=(Align.CENTER, Align.CENTER, Align.CENTER))


def test_the_pivot_is_inside_the_wall_below_the_rim():
    assert H.AXIS_Z < L.BASE_H
    assert H.AXIS_Y < H.y_out(H.AXIS_Z)


def test_each_station_is_one_leaf_with_a_pin_at_each_end():
    leaves = H.leaves()
    assert len(leaves.solids()) == len(H.STATIONS)
    for xs in H.STATIONS:
        for sgn, edge in H._ends(xs):
            # solid pin right on the axis, beyond the leaf end, inside the block's reach
            x = edge + sgn * (H.PIN_L - H.SIDE_CLR) / 2
            probe = _box(x, H.AXIS_Y, H.AXIS_Z, 1.0, H.PIN_R, H.PIN_R)
            assert (probe & leaves).volume >= probe.volume * (1 - 1e-4)


def test_the_leaf_is_flush_with_the_outer_wall():
    leaves = H.leaves()
    z = H.AXIS_Z
    xs = H.STATIONS[0]
    inside = _box(xs, H.y_out(z) - 0.2, z, 5, 0.2, 0.2)
    outside = _box(xs, H.y_out(z) + 0.2, z, 5, 0.2, 0.2)
    assert (inside & leaves).volume > 0
    assert (outside & leaves).volume < 1e-9


def test_the_socket_bores_clear_the_pins_and_open_upward_through_a_snap_neck():
    blocks = H.socket_blocks() - H.sockets()
    leaves = H.leaves()
    assert (blocks & leaves).volume < 1e-6              # the pins sit free in their bores
    for xs in H.STATIONS:
        for sgn, edge in H._ends(xs):
            x = edge + sgn * 2.5
            neck = _box(x, H.AXIS_Y, H.AXIS_Z + H.BORE_R + 1.0, 1.0, 2 * H.PIN_R - H.SNAP - 0.05, 1.0)
            assert (neck & blocks).volume < 1e-6        # open above the bore ...
            wide = _box(x, H.AXIS_Y, H.AXIS_Z + H.BORE_R + 1.0, 1.0, 2 * H.PIN_R, 1.0)
            assert (wide & blocks).volume > 1e-4        # ... through a neck narrower than the pin


def test_the_stop_lips_reach_into_the_notch_above_the_rim():
    blocks = H.socket_blocks()
    assert len(blocks.solids()) == 2 * len(H.STATIONS)  # each lip is joined to its block
    for xs in H.STATIONS:
        for sgn, edge in H._ends(xs):
            inside_notch = Pos(edge - sgn * H.LIP_W / 2, H.AXIS_Y - 5, L.BASE_H) * Box(
                H.LIP_W - 0.2, 10, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
            assert (inside_notch & blocks).volume > 0.1


def test_the_socket_blocks_print_without_supports():
    """Chins run the blocks' undersides into the wall at 45 degrees; all that
    still faces down is each lip's short ledge reaching into the notch, which
    the leaf sweeps under before the stop so it cannot have a chin."""
    from printability import span, steep_faces
    steep = steep_faces(H.socket_blocks())
    assert len(steep) == 2 * len(H.STATIONS)
    for f in steep:
        assert span(f) <= H.LIP_W + 1e-6
        assert f.center().Z > L.BASE_H                  # up at the lips, above the rim


def test_the_back_relief_raises_the_lid_off_the_rim_along_the_back():
    r = H.back_relief().bounding_box()
    assert math.isclose(r.max.Z, L.BASE_H + H.BACK_GAP, abs_tol=1e-6)
    assert r.min.Y < H.AXIS_Y and r.size.X > L.RIM.sx


def test_the_headlight_sits_forward_of_the_right_hand_recess():
    x0, x1, y0, y1 = L.device_footprint("ion")
    assert x1 > H.STATIONS[1] - H.NOTCH_W / 2 - H.BLOCK_W      # it is behind that hinge ...
    assert y1 <= H.RECESS_Y - 1.0 - 1.6                       # ... and clear of the recess wall


def test_opened_turns_the_lid_up_and_back():
    y, z = H.AXIS_Y - 10.0, H.AXIS_Z          # a point on the lid, 10 mm in front of the axis
    p = H.opened(90.0) * Pos(0, y, z)
    assert math.isclose(p.position.Y, H.AXIS_Y, abs_tol=1e-6)
    assert math.isclose(p.position.Z, H.AXIS_Z + 10.0, abs_tol=1e-6)
