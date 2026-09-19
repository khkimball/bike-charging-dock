import pytest
from build123d import Axis
from dock import cradles, params
from dock import measurements as m


@pytest.mark.parametrize("fn", [cradles.build_roam_cradle,
                                cradles.build_ion_cradle,
                                cradles.build_trackr_cradle])
def test_cradle_is_valid_and_sits_on_bed(fn):
    p = fn()
    assert p.is_valid  # property in build123d 0.12, not a method
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6


def test_ion_ring_inner_diameter_has_clearance():
    p = cradles.build_ion_cradle()
    # the ring's inner cylindrical face radius
    inner = [f for f in p.faces() if f.geom_type.name == "CYLINDER"]
    radii = sorted(f.radius for f in inner)
    assert abs(radii[0] - (m.ION.diameter / 2 + params.CLR_DEVICE)) < 1e-6


def test_trackr_pocket_wider_than_device():
    p = cradles.build_trackr_cradle()
    top = p.faces().sort_by(Axis.Z)[-1]
    inner = top.inner_wires()
    assert len(inner) == 1
    size = inner[0].bounding_box().size
    assert size.X >= m.TRACKR.width + 2 * params.CLR_DEVICE - 1e-6
    assert size.Y >= m.TRACKR.thickness + 2 * params.CLR_DEVICE - 1e-6


def test_every_cradle_has_a_floor_slot():
    for fn in (cradles.build_roam_cradle, cradles.build_ion_cradle,
               cradles.build_trackr_cradle):
        p = fn()
        bottom = p.faces().sort_by(Axis.Z)[0]
        assert len(bottom.inner_wires()) >= 1, fn.__name__
