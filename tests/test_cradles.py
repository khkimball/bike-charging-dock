import dataclasses
import math

import pytest
from build123d import Align, Axis, GeomType
from dock import cradles, params

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
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


def _roam_pocket_wall(p):
    """The pocket's low (-Y) wall, inner face: the biggest plane looking back
    up the slope at the device."""
    floor = _largest_upward_plane(p)
    n = floor.normal_at(floor.center())
    up = (0.0, n.Z, -n.Y)          # up-slope direction, floor normal rotated
    faces = [f for f in p.faces()
             if f.geom_type == GeomType.PLANE
             and f.normal_at(f.center()).Y * up[1]
             + f.normal_at(f.center()).Z * up[2] > 0.99]
    return max(faces, key=lambda f: f.area)


def test_roam_port_face_is_the_bottom_edge():
    """Wahoo puts the Roam 3's USB-C on the bottom edge, so the shelf floor
    must not be bored anywhere the device sits."""
    assert m.ROAM.port_face == "bottom"
    p = cradles.build_roam_cradle()
    floor = _largest_upward_plane(p)
    wall_y = _roam_pocket_wall(p).bounding_box().max.Y
    for w in floor.inner_wires():
        assert w.bounding_box().max.Y < wall_y, \
            "bottom-port Roam must not be bored under the device"


def test_roam_plug_lies_in_the_trough_with_its_tip_through_the_wall():
    """Measured on the solid: the USB-C overmold slides up the trough and
    through the pocket wall without fouling anything."""
    from build123d import Box, Pos, Rot
    p = cradles.build_roam_cradle()
    floor = _largest_upward_plane(p)
    n = floor.normal_at(floor.center())
    wall = _roam_pocket_wall(p).bounding_box()
    # floor point at the wall's inner face, and the two floor-frame axes
    y0, z0 = wall.max.Y, wall.min.Z
    up = (n.Z, -n.Y)                        # up the slope, in (Y, Z)
    off = (n.Y, n.Z)                        # off the floor, in (Y, Z)
    plug = params.USB_C_PLUG
    run = params.WALL + plug.length         # overmold, from the wall outward
    proud = 1.0                             # tip standing into the pocket
    s = (proud - run) / 2                   # centre of the plug, along the slope
    body = Box(plug.width, run + proud, plug.height, align=_CTR)
    at = Pos(0,
             y0 + up[0] * s + off[0] * plug.height / 2,
             z0 + up[1] * s + off[1] * plug.height / 2) * Rot(cradles.ROAM_TILT, 0, 0)
    placed = at * body
    assert (placed & p).volume < 1e-3, "the plug fouls the trough or the wall"
    # not vacuous: the plug really does reach through the wall into the pocket
    assert placed.bounding_box().max.Y > y0


def test_roam_bed_opening_is_the_cable_slot_in_front_of_the_wall():
    """The only bed-face opening is the cable drop at the trough's far end."""
    p = cradles.build_roam_cradle()
    bottom = p.faces().sort_by(Axis.Z)[0]
    inner = bottom.inner_wires()
    assert len(inner) == 1
    bb = inner[0].bounding_box()
    assert abs(bb.size.X - (params.USB_C_CABLE.width
                            + 2 * params.CLR_DEVICE)) < 1e-6
    assert abs(bb.size.Y - (params.USB_C_CABLE.height
                            + 2 * params.CLR_DEVICE)) < 1e-6
    assert bb.max.Y < _roam_pocket_wall(p).bounding_box().min.Y


def test_roam_com_projects_inside_the_pocket_floor_when_tilted():
    """With only 0.6 of its length held, the Roam must still not tip out: its
    centre of mass has to fall inside the tilted pocket floor."""
    p = cradles.build_roam_cradle()
    floor = _largest_upward_plane(p)
    lo_y = _roam_pocket_wall(p).bounding_box().max.Y   # floor edge at the wall
    hi_y = floor.bounding_box().max.Y
    t = math.radians(cradles.ROAM_TILT)
    # the device lies on the floor, bottom edge against the low (-Y) wall
    com_y = (lo_y
             + (m.ROAM.length / 2) * math.cos(t)        # along the floor
             - (m.ROAM.thickness / 2) * math.sin(t))    # off the floor
    assert lo_y <= com_y <= hi_y, (
        f"CoM projects to y={com_y:.1f}, pocket floor spans "
        f"{lo_y:.1f}..{hi_y:.1f}")


def test_roam_back_port_variant_keeps_the_floor_bore(monkeypatch):
    """A back-mounted port still gets the original bore through the floor."""
    monkeypatch.setattr(m, "ROAM",
                        dataclasses.replace(m.ROAM, port_face="back"))
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
