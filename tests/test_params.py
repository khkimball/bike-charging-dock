from pathlib import Path

from build123d import Box

from dock import params
from dock.export import write_all


def test_design_rules_match_spec():
    assert params.WALL == 2.4
    assert params.FLOOR == 1.6
    assert params.CLR_DEVICE == 0.3
    assert params.CLR_FIT == 0.2
    assert params.CLR_RAIL == 0.25
    assert (params.BED_X, params.BED_Y) == (250, 120)


def test_plug_sizes_are_positive():
    for plug in (params.USB_A_PLUG, params.USB_C_PLUG, params.MICRO_PLUG):
        assert plug.width > 0 and plug.height > 0 and plug.length > 0


def test_write_all_creates_three_files(tmp_path: Path):
    paths = write_all(Box(10, 10, 10), "cube", tmp_path)
    assert [p.suffix for p in paths] == [".stl", ".3mf", ".step"]
    assert all(p.stat().st_size > 0 for p in paths)
