import math

import pytest
from build123d import Axis, GeomType
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


def _largest_upward_plane(p):
    """The shelf/pocket floor: the biggest plane whose normal points up."""
    ups = [f for f in p.faces()
           if f.geom_type == GeomType.PLANE and f.normal_at(f.center()).Z > 0.1]
    return max(ups, key=lambda f: f.area)


def test_roam_shelf_tilts_toward_the_user():
    """The shelf floor must tip toward -Y; Rot(-20) would flip this sign."""
    p = cradles.build_roam_cradle()
    n = _largest_upward_plane(p).normal_at(_largest_upward_plane(p).center())
    assert n.Y < 0, "shelf must tip toward the user (-Y), not away"
    assert abs(n.Y + math.sin(math.radians(cradles.ROAM_TILT))) < 1e-3
    assert abs(n.Z - math.cos(math.radians(cradles.ROAM_TILT))) < 1e-3


def test_roam_open_end_is_the_high_end():
    """The pocket is open at +Y, which must be the raised end."""
    p = cradles.build_roam_cradle()
    floor = _largest_upward_plane(p)
    bb = floor.bounding_box()
    lo = [v for v in floor.vertices() if v.Y < (bb.min.Y + bb.max.Y) / 2]
    hi = [v for v in floor.vertices() if v.Y > (bb.min.Y + bb.max.Y) / 2]
    assert min(v.Z for v in hi) > max(v.Z for v in lo)


def test_roam_slot_lies_wholly_inside_the_pocket_floor():
    """A closed rectangular inner wire proves the slot clears the pocket wall."""
    p = cradles.build_roam_cradle()
    inner = _largest_upward_plane(p).inner_wires()
    assert len(inner) == 1
    w = params.USB_C_PLUG.width + 2 * params.CLR_DEVICE
    h = params.USB_C_PLUG.height + 2 * params.CLR_DEVICE
    assert abs(inner[0].length - 2 * (w + h)) < 1e-6


def _has_chamfer(p) -> bool:
    for f in p.faces():
        if f.geom_type == GeomType.CONE:      # chamfer on a circular edge
            return True
        if f.geom_type == GeomType.PLANE:
            n = f.normal_at(f.center())
            if n.Z < -1e-6:
                tilt = math.degrees(math.acos(min(1.0, -n.Z)))
                if abs(tilt - 45.0) < 1e-3:
                    return True
    return False


@pytest.mark.parametrize("fn", [cradles.build_roam_cradle,
                                cradles.build_ion_cradle,
                                cradles.build_trackr_cradle])
def test_every_cradle_has_a_bottom_chamfer(fn):
    assert _has_chamfer(fn()), f"{fn.__name__} has no CHAMFER on its bed edges"


def test_roam_wedge_front_is_not_a_knife_edge():
    """The thin front of the ramp must end in a printable vertical face."""
    p = cradles.build_roam_cradle()
    bb = p.bounding_box()
    front = [f for f in p.faces()
             if f.geom_type == GeomType.PLANE
             and abs(f.normal_at(f.center()).Z) < 1e-6          # vertical
             and f.normal_at(f.center()).Y < -0.99              # faces -Y
             and f.center().Z < bb.min.Z + cradles.ROAM_TOE]
    assert front, "no vertical face at the front of the wedge"
    assert max(f.bounding_box().size.Z for f in front) >= 0.8
