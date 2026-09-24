from pathlib import Path

from build123d import Box

from dock import params
from dock.export import write_all


def test_design_rules_match_spec():
    assert params.WALL == 2.0
    assert params.THIN_WALL == 1.6
    assert params.FLOOR == 1.2
    assert params.CLR_FIT == 0.15
    assert params.CLR_BAY == 8.0
    assert params.CLR_BAY_OUTER == 3.0
    assert params.TRAY_PLATE == 1.2
    assert params.LID_PLATE == 1.2
    assert params.BAY_DEPTH == 38.0
    assert params.TAPER_DEG == 15.0
    assert params.CORNER_R == 30.0
    assert params.BAND_H == 8.0
    assert (params.BED_X, params.BED_Y) == (250, 250)
    # removed with the removable dividers and the last v1 module
    assert not hasattr(params, "CLR_RAIL")
    for name in ("V1_WALL", "V1_FLOOR", "V1_CORNER_R", "V1_TRAY_PLATE"):
        assert not hasattr(params, name)


def test_plug_sizes_are_positive():
    for plug in (params.USB_A_PLUG, params.USB_C_PLUG, params.MICRO_PLUG):
        assert plug.width > 0 and plug.height > 0 and plug.length > 0


def test_write_all_creates_stl_and_step(tmp_path: Path):
    paths = write_all(Box(10, 10, 10), "cube", tmp_path)
    assert [p.suffix for p in paths] == [".stl", ".step"]
    assert all(p.stat().st_size > 0 for p in paths)
