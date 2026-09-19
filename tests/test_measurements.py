from dock import measurements as m


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


def test_slab_port_height_defaults_to_mid_thickness():
    """An unmeasured port_height means the port is on the device mid-plane."""
    import dataclasses
    assert m.ROAM.port_height is None
    assert m.ROAM.port_center_height == m.ROAM.thickness / 2
    measured = dataclasses.replace(m.ROAM, port_height=7.0)
    assert measured.port_center_height == 7.0
