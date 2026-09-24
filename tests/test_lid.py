"""Lid tests: measured on the built solid, in print orientation and seated."""
import math
from functools import lru_cache

from build123d import Align, Box, Pos

from dock import hinge as H, layout as L, lid, params, taper
from printability import span, steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)


@lru_cache(maxsize=None)
def _printed():
    return lid.build_lid()


@lru_cache(maxsize=None)
def _seated():
    return lid.lid_seat() * _printed()


def _slab(p, z, thick=2e-3):
    return p & (Pos(0, 0, z) * Box(400, 400, thick, align=_CTR))


def _front_y(p, z):
    """Y of the lid's front (-Y) face at height z: clear of the hinge side."""
    return _slab(p, z).bounding_box().min.Y


def test_lid_is_one_valid_solid_on_the_bed():
    p = _printed()
    assert p.is_valid and len(p.solids()) == 1
    assert abs(p.bounding_box().min.Z) < 1e-6


def test_lid_fits_the_bed():
    s = _printed().bounding_box().size
    assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_the_lid_meets_the_rim_flush():
    z = L.BASE_H + 0.01
    sx, sy, _ = L.RIM.at(z)
    bb = _slab(_seated(), z).bounding_box()
    assert math.isclose(bb.size.X, sx, abs_tol=0.02)
    assert math.isclose(bb.min.Y, -sy / 2, abs_tol=0.02)


def test_the_slope_continues_the_base_taper():
    z0, z1 = L.BASE_H + 0.5, L.BASE_H + L.LID_SLOPE_H - 0.5
    lean = (_front_y(_seated(), z0) - _front_y(_seated(), z1)) / (z1 - z0)
    assert math.isclose(lean, taper.TAN, abs_tol=1e-3)


def test_the_lip_stands_proud_of_the_slope():
    z_slope = L.BASE_H + L.LID_SLOPE_H
    below = _front_y(_seated(), z_slope - 0.01)
    above = _front_y(_seated(), z_slope + 0.5)
    assert math.isclose(below - above, L.LIP_W, abs_tol=0.02)


def test_the_walls_are_a_thin_wall_thick_square_to_the_slope():
    z = L.BASE_H + 2.0
    y_out = -L.RIM.at(z)[1] / 2
    w = lid.WALL_H
    probe = lambda y, t: Pos(0, y, z) * Box(4, t, 0.02, align=_CTR)
    assert (probe(y_out + w / 2, w - 0.1) & _seated()).volume >= probe(0, w - 0.1).volume * (1 - 1e-4)
    assert (probe(y_out + w + 0.1, 0.1) & _seated()).volume < 1e-9


def test_the_plate_is_lid_plate_thick():
    top = L.BASE_H + L.LID_H
    col = lambda z0, z1: Pos(0, 0, z0) * Box(2, 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    solid = col(top - params.LID_PLATE + 0.02, top - 0.02)
    air = col(L.BASE_H + 0.5, top - params.LID_PLATE - 0.02)
    assert (solid & _seated()).volume >= solid.volume * (1 - 1e-4)
    assert (air & _seated()).volume < 1e-6


def test_the_lid_prints_with_only_the_leaf_pins_overhanging():
    for f in steep_faces(_printed()):
        c = f.center()
        near = min(abs(abs(c.X - xs) - H.NOTCH_W / 2) for xs in H.STATIONS)
        assert near <= H.PIN_L + 1e-6, f"overhang away from a pin at {c}"
        assert span(f) <= H.PIN_L + 1.0


def test_the_lid_is_raised_off_the_rim_along_the_back():
    y = L.RIM.sy / 2 - 1.0                    # over the back rim, between the stations
    probe = Pos(0, y, L.BASE_H + H.BACK_GAP / 2) * Box(20, 1, H.BACK_GAP - 0.2, align=_CTR)
    assert (probe & _seated()).volume < 1e-9
    front = Pos(0, -y, L.BASE_H + 0.3) * Box(20, 1, 0.4, align=_CTR)
    assert (front & _seated()).volume > 0     # but it sits on the rim at the front


def test_the_leaves_hang_into_the_notches():
    for xs in H.STATIONS:
        probe = Pos(xs, H.y_out(H.AXIS_Z) - 1.0, H.AXIS_Z) * Box(10, 1, 1, align=_CTR)
        assert (probe & _seated()).volume >= probe.volume * (1 - 1e-4)
