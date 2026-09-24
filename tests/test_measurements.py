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


def test_charger_is_a_flat_six_port_desktop_charger():
    # sanity envelope for an Anker A2154; fails loudly if someone types cm
    assert 70 < m.CHARGER.port_face_width < 100
    assert 60 < m.CHARGER.port_to_inlet < 95
    assert 25 < m.CHARGER.height < 40


def test_the_six_ports_fit_on_the_port_face():
    """One row of six: five pitches plus the two end margins have to land
    inside the port face, and the row is centred on it."""
    c = m.CHARGER
    span = 5 * c.port_pitch
    assert c.port_pitch > 0
    assert 2 * c.port_face_margin + span <= c.port_face_width + 1e-9
    assert abs(c.port_face_margin - (c.port_face_width - span) / 2) < 0.1


def test_the_inlet_sits_inside_the_charger_body():
    assert 0 < m.CHARGER.inlet_center_z < m.CHARGER.height


def test_this_charger_has_no_status_led():
    """The A2154 has no LED anywhere on it.  None is how that is recorded,
    and it is what tells the base to leave its +X end wall blind."""
    assert m.CHARGER.led_offset_from_ports is None


def test_devices_are_slabs_with_published_sizes():
    assert m.ROAM == Slab(96.0, 53.0, 24.0)
    assert m.ION.width == 34.7 and m.ION.thickness == 30.2
    assert m.TRACKR.length == 89.9


def test_the_charger_edge_radius_fits_the_body():
    c = m.CHARGER
    assert 0 < c.edge_r < c.height / 2
