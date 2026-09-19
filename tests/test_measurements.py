from dock import measurements as m


def test_all_measurements_positive():
    for obj in (m.ROAM, m.ION, m.TRACKR, m.CHARGER):
        for k, v in vars(obj).items():
            if isinstance(v, str):
                continue
            assert v > 0, f"{type(obj).__name__}.{k} must be > 0"


def test_charger_is_powerport6_sized():
    # sanity envelope for an Anker A2123; fails loudly if someone types cm
    assert 85 < m.CHARGER.port_face_width < 110
    assert 55 < m.CHARGER.port_to_inlet < 75
    assert 20 < m.CHARGER.height < 32
