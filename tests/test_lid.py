"""Lid tests.  Everything is measured on the built solid -- faces, wires,
bounding boxes and probe intersections -- never a restatement of a constant."""
import math

from build123d import Align, Axis, Box, GeomType, Pos

from dock import base, lid, params

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)


# --- helpers: everything below reads the solid -------------------------------

def _top_face(p):
    """The skirt's top rim: the highest horizontal, upward-facing face."""
    ups = [f for f in p.faces().filter_by(Axis.Z) if f.normal_at().Z > 0]
    return max(ups, key=lambda f: f.center().Z)


def _cavity_floor(p):
    """The underside of the top plate, seen from inside the skirt: the lowest
    horizontal upward face that is not the bed face."""
    bed_z = p.bounding_box().min.Z
    ups = [f for f in p.faces().filter_by(Axis.Z)
           if f.normal_at().Z > 0 and f.center().Z > bed_z + 1e-6]
    return min(ups, key=lambda f: f.center().Z)


def _skirt_opening(p):
    """Bounding box of the skirt's inner wire, read off the top rim face."""
    inner = _top_face(p).inner_wires()
    assert len(inner) == 1, f"expected one skirt opening, found {len(inner)}"
    return inner[0].bounding_box()


def _slab(p, z, thick=0.2):
    """Horizontal cross-section of the part at height z."""
    bb = p.bounding_box()
    probe = Pos(bb.center().X, bb.center().Y, z) * Box(
        4 * bb.size.X, 4 * bb.size.Y, thick, align=_CTR)
    return p & probe


def _is_solid_in(probe, p):
    return abs((probe & p).volume - probe.volume) < 1e-3


# --- the printed lid ---------------------------------------------------------

def test_lid_is_one_valid_solid_on_the_bed():
    p = lid.build_lid()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert abs(bb.size.Z - lid.LID_H) < 1e-6


def test_lid_wraps_the_base_outside_with_a_wall_and_fit_clearance():
    """The lid drops over the OUTSIDE of the base: one wall plus the fit
    clearance beyond the base's footprint, on every side."""
    s = lid.build_lid().bounding_box().size
    over = params.V1_WALL + params.CLR_FIT
    assert abs(s.X - (base.BASE_X + 2 * over)) < 1e-6
    assert abs(s.Y - (base.BASE_Y + 2 * over)) < 1e-6


def test_lid_fits_the_bed():
    s = lid.build_lid().bounding_box().size
    assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_skirt_opening_clears_the_base_by_the_fit_clearance():
    bb = _skirt_opening(lid.build_lid())
    assert abs(bb.size.X - (base.BASE_X + 2 * params.CLR_FIT)) < 1e-6
    assert abs(bb.size.Y - (base.BASE_Y + 2 * params.CLR_FIT)) < 1e-6


def test_plate_is_one_wall_thick_and_the_skirt_stands_clear_of_it():
    """Measured between the bed face, the cavity floor and the skirt rim."""
    p = lid.build_lid()
    floor_z = _cavity_floor(p).center().Z
    assert abs(floor_z - params.V1_WALL) < 1e-6
    assert abs(_top_face(p).center().Z - floor_z - lid.SKIRT_H) < 1e-6


def test_skirt_is_one_wall_thick_all_round():
    """At mid-skirt height the section is a closed ring exactly WALL thick:
    solid from the opening out to the outer face, open just inside it."""
    p = lid.build_lid()
    ring = _slab(p, params.V1_WALL + lid.SKIRT_H / 2)
    assert len(ring.solids()) == 1
    top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    assert len(top.inner_wires()) == 1, "the skirt is not a closed ring"
    bb = top.inner_wires()[0].bounding_box()
    assert abs(bb.size.X - (base.BASE_X + 2 * params.CLR_FIT)) < 1e-6
    outer = top.bounding_box()
    assert abs((outer.size.X - bb.size.X) / 2 - params.V1_WALL) < 1e-6
    assert abs((outer.size.Y - bb.size.Y) / 2 - params.V1_WALL) < 1e-6


def test_outer_vertical_corners_are_rounded():
    p = lid.build_lid()
    cyl = [f for f in p.faces()
           if f.geom_type == GeomType.CYLINDER
           and abs(f.radius - lid.OUTER_R) < 1e-6]
    assert len(cyl) >= 4


def test_skirt_inner_corners_are_concentric_with_the_base_corners():
    """The inner corner arcs are CORNER_R + CLR_FIT and share their centres
    with the outer OUTER_R arcs, so the gap is uniform through the corners.
    Each arc centre is read off the solid: `radius` in from the face's own
    midpoint, along its normal, toward the middle of the part."""
    p = lid.build_lid()
    mid = p.bounding_box().center()

    def arcs(r):
        return [f for f in p.faces()
                if f.geom_type == GeomType.CYLINDER and abs(f.radius - r) < 1e-6]

    def centre(f):
        c, n = f.center(), f.normal_at()
        u = n if (mid.X - c.X) * n.X + (mid.Y - c.Y) * n.Y > 0 else -n
        return (round(c.X + u.X * f.radius, 3), round(c.Y + u.Y * f.radius, 3))

    inner, outer = arcs(params.V1_CORNER_R + params.CLR_FIT), arcs(lid.OUTER_R)
    assert len(inner) >= 4 and len(outer) >= 4
    assert {centre(f) for f in inner} == {centre(f) for f in outer}


def test_plate_outer_edge_is_chamfered_not_filleted():
    """The plate face lies on the bed when printing, so its outer edge is a
    downward edge: a chamfer, CHAMFER in from the outer profile all round."""
    p = lid.build_lid()
    bb = p.bounding_box().size
    bed = p.faces().sort_by(Axis.Z)[0]
    fb = bed.bounding_box().size
    assert abs(fb.X - (bb.X - 2 * params.CHAMFER)) < 1e-6
    assert abs(fb.Y - (bb.Y - 2 * params.CHAMFER)) < 1e-6
    assert not bed.inner_wires()
    flats = [f for f in p.faces()
             if f.geom_type == GeomType.PLANE
             and abs(math.degrees(math.acos(min(1.0, abs(f.normal_at().Z)))) - 45.0) < 1e-6]
    assert len(flats) >= 4, "no 45 degree chamfer flats on the plate edge"


def test_the_lid_prints_with_no_overhang_at_all():
    """Plate-down, skirt up: every downward face is the bed face or a 45
    degree chamfer, so there is no bridge and no unsupported ceiling."""
    p = lid.build_lid()
    bed_z = p.bounding_box().min.Z
    for f in p.faces():
        n = f.normal_at()
        if n.Z >= -1e-6 or abs(f.center().Z - bed_z) < 1e-6:
            continue
        overhang = math.degrees(math.asin(min(1.0, -n.Z)))
        assert overhang <= 45.0 + 1e-6, (
            f"{overhang:.1f} deg overhang at {f.center()}")


# --- seated on the base ------------------------------------------------------

def test_lid_seats_over_the_base_without_interference():
    p = base.build_base()
    seated = lid.lid_seat() * lid.build_lid()
    assert (seated & p).volume < 1e-3
    bb = seated.bounding_box()
    over = params.V1_WALL + params.CLR_FIT
    assert abs(bb.min.X + over) < 1e-6
    assert abs(bb.max.X - (base.BASE_X + over)) < 1e-6
    assert abs(bb.center().Y) < 1e-6
    assert abs(bb.min.Z - (base.BASE_H - lid.SKIRT_H)) < 1e-6
    assert abs(bb.max.Z - (base.BASE_H + params.V1_WALL)) < 1e-6


def test_seated_lid_rests_on_the_base_rim():
    """The plate's underside is level with the base's top face, so the lid
    lands on the rim rather than hanging off the skirt: a probe straddling
    that height on the rim ring is base below and lid above."""
    p = base.build_base()
    seated = lid.lid_seat() * lid.build_lid()
    rim_z = p.bounding_box().max.Z
    unders = [f for f in seated.faces().filter_by(Axis.Z)
              if f.normal_at().Z < 0 and abs(f.center().Z - rim_z) < 1e-6]
    assert unders, "nothing of the lid sits on the base rim"
    # on the rim ring, half a wall in from the base's +Y outer face
    y = base.BASE_Y / 2 - params.V1_WALL / 2

    def probe(z0, h):
        return Pos(base.BASE_X / 2, y, z0 + h / 2) * Box(
            20, params.V1_WALL - 0.02, h, align=_CTR)

    assert _is_solid_in(probe(rim_z - 0.2, 0.2), p), "no rim under the lid"
    assert _is_solid_in(probe(rim_z + 0.05, 0.2), seated), "the lid is not on it"


def test_seated_skirt_hangs_down_the_outside_of_the_base():
    """At mid-skirt height the skirt is beside the base, not on top of it:
    a band one wall thick, starting CLR_FIT out from the base's side face."""
    p = base.build_base()
    seated = lid.lid_seat() * lid.build_lid()
    z = base.BASE_H - lid.SKIRT_H / 2
    y0 = base.BASE_Y / 2 + params.CLR_FIT
    skirt = Pos(base.BASE_X / 2, y0 + params.V1_WALL / 2, z) * Box(
        20, params.V1_WALL - 0.02, 1.0, align=_CTR)
    assert _is_solid_in(skirt, seated), "the skirt does not reach down the side"
    gap = Pos(base.BASE_X / 2, base.BASE_Y / 2 + params.CLR_FIT / 2, z) * Box(
        20, params.CLR_FIT - 0.02, 1.0, align=_CTR)
    assert (gap & seated).volume < 1e-3 and (gap & p).volume < 1e-3
