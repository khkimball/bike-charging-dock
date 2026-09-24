"""The parts together: tray in the base, lid on the rim, lid swinging."""
import math
from functools import lru_cache

from build123d import Align, Box, Pos

from dock import base, hinge as H, layout as L, lid, params, taper, tray

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


@lru_cache(maxsize=None)
def _base():
    return base.build_base()


@lru_cache(maxsize=None)
def _tray():
    return base.tray_seat() * tray.build_tray()


@lru_cache(maxsize=None)
def _printed_lid():
    return lid.build_lid()


def _lid(deg=0.0):
    return lid.lid_seat(deg) * _printed_lid()


def _hit(a, b):
    return (a & b).volume


def test_the_tray_seats_in_the_base_on_the_ledge():
    assert _hit(_tray(), _base()) < 1e-3
    assert _hit(Pos(0, 0, -0.2) * _tray(), _base()) > 1e-3


def test_the_tray_rim_sits_just_below_the_base_rim():
    assert math.isclose(L.BASE_H - _tray().bounding_box().max.Z, L.TRAY_SINK, abs_tol=0.01)


def test_the_closed_lid_rests_on_the_rim_clear_of_everything():
    assert _hit(_lid(), _base()) < 1e-3
    assert _hit(_lid(), _tray()) < 1e-3
    assert _hit(Pos(0, 0, -0.2) * _lid(), _base()) > 1e-3


def test_devices_on_the_seated_tray_clear_the_closed_lid():
    for name, dev in L.DEVICES.items():
        x0, x1, y0, y1 = L.device_footprint(name)
        box = Pos((x0 + x1) / 2, (y0 + y1) / 2, L.TRAY_Z0 + params.TRAY_PLATE + 0.01) * Box(
            x1 - x0, y1 - y0, dev.thickness, align=_MIN)
        assert _hit(box, _lid()) < 1e-6, name
        assert _hit(box, _tray()) < 1e-6, name


def test_the_lid_swings_open_clear_of_the_base_and_tray():
    for deg in (5, 20, 40, 60, 80, 100, H.OPEN_DEG - 2):
        assert _hit(_lid(deg), _base()) < 1e-3, deg
        assert _hit(_lid(deg), _tray()) < 1e-3, deg


def test_the_heel_stops_the_lid_just_past_open():
    assert _hit(_lid(H.OPEN_DEG + 3), _base()) > 1e-3


def test_a_closed_lid_lifted_catches_on_the_pins():
    assert _hit(Pos(0, 0, 1.0) * _lid(), _base()) > 1e-3


def test_at_full_open_the_lid_lifts_off_along_the_wall_over_the_snap():
    t = math.radians(params.TAPER_DEG)
    def lifted(s):
        return Pos(0, s * math.sin(t), s * math.cos(t)) * _lid(H.OPEN_DEG - 1)
    assert _hit(lifted(H.BORE_R), _base()) > 1e-3             # the neck snaps over the pin
    assert _hit(lifted(2 * H.BORE_R + 2.0), _base()) < 1e-3   # and then it is off


def test_the_assembled_dock_fits_the_bed_footprint():
    for part in (_base(), _tray(), _lid()):
        s = part.bounding_box().size
        assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_cables_drop_at_least_15_mm_clear_below_every_cutout():
    for _, cx, cy, sx, sy in L.cutouts():
        col = Pos(cx, cy, L.TRAY_Z0 - 15.0) * Box(sx - 0.02, sy - 0.02, 15.0 - 0.01, align=_MIN)
        assert _hit(col, _base()) < 1e-3, (cx, cy)
