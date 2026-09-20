from dock import measurements as m
from dock.measurements import Slab


def test_all_measurements_positive():
    for obj in (m.ROAM, m.ION, m.TRACKR, m.CHARGER):
        for k, v in vars(obj).items():
            if isinstance(v, str):
                continue
            if v is None:
                continue          # an optional measurement, left unmeasured
            assert v > 0, f"{type(obj).__name__}.{k} must be > 0"


def test_charger_is_powerport6_sized():
    # sanity envelope for an Anker A2123; fails loudly if someone types cm
    assert 85 < m.CHARGER.port_face_width < 110
    assert 55 < m.CHARGER.port_to_inlet < 75
    assert 20 < m.CHARGER.height < 32


def test_devices_are_slabs_with_published_sizes():
    assert m.ROAM == Slab(96.0, 53.0, 24.0)
    assert m.ION.width == 34.7 and m.ION.thickness == 30.2
    assert m.TRACKR.length == 89.9
