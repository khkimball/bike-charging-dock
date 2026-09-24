import math

from build123d import Axis, GeomType

from dock import params, taper


def _circle_radii(face):
    return sorted({round(e.radius, 3) for e in face.edges()
                   if e.geom_type == GeomType.CIRCLE})


def test_the_draft_is_the_spec_angle():
    assert math.isclose(math.degrees(math.atan(taper.TAN)), params.TAPER_DEG)


def test_a_drafted_solid_leans_by_the_draft_on_every_side():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    p = o.solid(10.0, 50.0)
    faces = p.faces().sort_by(Axis.Z)
    bottom, top = faces[0].bounding_box().size, faces[-1].bounding_box().size
    lean = 40.0 * math.tan(math.radians(params.TAPER_DEG))
    assert math.isclose(top.X - bottom.X, 2 * lean, abs_tol=1e-4)
    assert math.isclose(top.Y - bottom.Y, 2 * lean, abs_tol=1e-4)


def test_the_corner_radius_shrinks_with_the_draft_so_corners_stay_concentric():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    p = o.solid(10.0, 50.0)
    faces = p.faces().sort_by(Axis.Z)
    lean = 40.0 * taper.TAN
    assert _circle_radii(faces[-1]) == [20.0]
    assert _circle_radii(faces[0]) == [round(20.0 - lean, 3)]


def test_an_inset_outline_is_a_wall_thickness_in_from_it():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    outer = o.solid(0.0, 50.0).faces().sort_by(Axis.Z)[-1].bounding_box().size
    inner = o.solid(0.0, 50.0, inset=taper.horiz(2.0)).faces().sort_by(Axis.Z)[-1].bounding_box().size
    # measured square to the drafted face, the wall is 2.0 thick
    assert math.isclose((outer.X - inner.X) / 2 * taper.COS, 2.0, abs_tol=1e-4)


def test_above_its_reference_height_an_outline_grows():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=0.0)
    sx, sy, r = o.at(10.0)
    assert sx > 100.0 and sy > 60.0 and r > 20.0


def test_corner_rect_rounds_each_corner_by_its_own_radius():
    s = taper.corner_rect(0, 40, 0, 30, {"--": 10.0, "+-": 3.0, "++": 0.0, "-+": 5.0}, z=0)
    assert _circle_radii(s.faces()[0]) == [3.0, 5.0, 10.0]


def test_bed_chamfer_inset_makes_a_45_degree_foot_on_a_drafted_wall():
    o = taper.Outline(100.0, 60.0, 20.0, z_ref=50.0)
    lo = o.at(0.0, taper.bed_chamfer_inset())[0]
    hi = o.at(params.CHAMFER)[0]
    assert math.isclose((hi - lo) / 2, params.CHAMFER, abs_tol=1e-9)
