"""Base tests: everything read off the built solid."""
import math
from functools import lru_cache

from build123d import Align, Axis, Box, Cylinder, Plane, Pos, SlotCenterToCenter, extrude, fillet

from dock import measurements as m
from dock import base, hinge as H, layout as L, params, taper
from printability import span, steep_faces

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
MAX_BRIDGE = 20.0


@lru_cache(maxsize=None)
def _base():
    return base.build_base()


def _slab(p, z, thick=2e-3):
    return p & (Pos(0, 0, z) * Box(400, 400, thick, align=_CTR))


def _section_face(p, z):
    """The part's cross-section at height z, as one face: the biggest
    upward face of a hair-thin slab there."""
    faces = [f for f in _slab(p, z).faces() if f.normal_at().Z > 0.99]
    return max(faces, key=lambda f: f.area)


def _solid(probe):
    return (probe & _base()).volume >= probe.volume * (1 - 1e-4)


def _clear(probe):
    return (probe & _base()).volume < probe.volume * 1e-6


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=_CTR)


def _charger(dx=0.0, dy=0.0):
    c = m.CHARGER
    body = Box(c.port_to_inlet, c.port_face_width, c.height, align=(Align.MIN, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Z), c.corner_r)
    return Pos(base.POCKET_MIN_X + params.CLR_FIT + dx, dy, params.FLOOR) * body


# --- shell --------------------------------------------------------------------

def test_base_is_one_valid_solid_on_the_bed_and_fits_it():
    p = _base()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert bb.size.X <= params.BED_X and bb.size.Y <= params.BED_Y


def test_the_rim_is_the_layout_rim():
    z = L.BASE_H - 0.01
    sx, sy, _ = L.RIM.at(z)
    bb = _slab(_base(), z).bounding_box()
    assert math.isclose(bb.size.X, sx, abs_tol=0.02)
    assert math.isclose(bb.min.Y, -sy / 2, abs_tol=0.02)
    assert _clear(_box(0, -sy / 2 + 1.0, L.BASE_H + 0.5, 10, 1, 0.5))


def test_every_side_leans_at_the_draft():
    for axis, z0, z1 in (("-Y", 20, 70), ("+X", 20, 70), ("-X", 30, 70)):
        def edge(z):
            bb = _slab(_base(), z).bounding_box()
            return {"-Y": -bb.min.Y, "+X": bb.max.X, "-X": -bb.min.X}[axis]
        lean = (edge(z1) - edge(z0)) / (z1 - z0)
        assert math.isclose(lean, taper.TAN, abs_tol=1e-3), axis


def test_corners_run_from_r30_at_the_rim_toward_r8_at_the_foot():
    from build123d import GeomType
    for z in (L.BASE_H - 1.0, params.CHAMFER + 1.0):
        top = _section_face(_base(), z)
        radii = [e.radius for e in top.outer_wire().edges() if e.geom_type == GeomType.CIRCLE]
        assert math.isclose(max(radii), L.RIM.at(z)[2], abs_tol=0.02), z
    assert L.RIM.at(0.0)[2] > 7.5


def test_the_wall_is_one_wall_thick_square_to_the_slope():
    z = 60.0
    top = _section_face(_base(), z)
    outer = top.outer_wire().bounding_box().min.Y
    inner = min(w.bounding_box().min.Y for w in top.inner_wires())
    assert math.isclose((inner - outer) * taper.COS, params.WALL, abs_tol=0.02)


def test_the_floor_is_floor_thick():
    x = base.FENCE_MAX_X + 20.0 + base.TIE_PITCH / 2   # between tie holes
    assert _solid(_box(x, 0, params.FLOOR / 2, 1, 1, params.FLOOR - 0.04))
    assert _clear(_box(x, 0, params.FLOOR + 1.0, 1, 1, 1.0))


# --- tray ledge ---------------------------------------------------------------

def test_the_ledge_is_a_ledge_wide_shelf_at_the_tray_underside():
    z = base.LEDGE_Z
    top = _section_face(_base(), z - 0.01)
    shelf = min(w.bounding_box().min.Y for w in top.inner_wires())
    wall = L.RIM.at(z, taper.horiz(params.WALL))[1] / 2
    assert math.isclose(shelf + wall, base.LEDGE_W, abs_tol=0.03)
    assert _clear(_box(0, -wall + 1.0, z + 0.5, 20, 1.0, 0.5))


# --- colour groove ------------------------------------------------------------

def test_the_colour_groove_is_cut_at_the_band_height():
    def front(z):
        return -_slab(_base(), z).bounding_box().min.Y
    sy = lambda z: L.RIM.at(z)[1] / 2
    assert math.isclose(sy(params.BAND_H) - front(params.BAND_H), base.GROOVE_D, abs_tol=0.02)
    for z in (params.BAND_H - 1.0, params.BAND_H + 1.5):
        assert math.isclose(front(z), sy(z), abs_tol=0.02)


# --- charger fence --------------------------------------------------------------

def test_the_charger_fits_the_pocket_with_fit_clearance():
    assert (_charger() & _base()).volume < 1e-6
    assert (_charger(dx=params.CLR_FIT + 0.1) & _base()).volume > 1e-3
    assert (_charger(dy=params.CLR_FIT + 0.1) & _base()).volume > 1e-3
    assert (_charger(dx=-(base.POCKET_BACK_SLACK + params.CLR_FIT + 0.1)) & _base()).volume > 1e-3


def test_the_pocket_corners_follow_the_charger_corners():
    c = m.CHARGER
    x = base.POCKET_MAX_X
    y = base.POCKET_Y / 2
    d = 0.2 * base.POCKET_R           # inside the fillet: solid; a square corner would be air
    assert _solid(_box(x - d, y - d, params.FLOOR + 1.0, 0.1, 0.1, 0.5))


def test_the_fence_has_no_fingernail_notch():
    y = base.POCKET_Y / 2 + params.WALL / 2
    x0, x1 = base.FENCE_MIN_X + 2.0, base.POCKET_MAX_X - base.POCKET_R
    assert _solid(_box((x0 + x1) / 2, y, params.FLOOR + base.FENCE_H / 2, x1 - x0, 0.5, base.FENCE_H - 0.2))


def test_room_in_front_of_the_ports_for_the_plugs():
    x = base.POCKET_MAX_X + params.WALL + 0.5
    room = base.CAVITY_MAX_X - base.POCKET_MAX_X
    assert room >= base.PORT_PLUG_ROOM_MIN
    probe = _box(x + (room - params.WALL - 1.0) / 2, 0, params.FLOOR + 5.0,
                 room - params.WALL - 1.0, 20.0, 8.0)
    assert _clear(probe)


# --- wall openings ----------------------------------------------------------------

def _through_minus_x(y, z, sy, sz):
    x0 = -L.RIM.sx / 2 - 1.0
    return Pos(x0, y, z) * Box(base.CAVITY_MIN_X - x0 + 0.5, sy, sz, align=(Align.MIN, Align.CENTER, Align.CENTER))


def _wall_x(z, margin=0.2):
    """Midpoint X and thickness (a hair inside each face) of the -X wall's
    cross-section at height z."""
    outer = -L.RIM.at(z)[0] / 2
    inner = -L.RIM.at(z, base.WALL_H)[0] / 2
    return (outer + inner) / 2, inner - outer - 2 * margin


def _wall_solid(y, z, sy, sz):
    """True if the -X wall's full thickness is solid material at (y, z),
    over a sy x sz patch (a probe confined to the wall, not through it)."""
    cx, sx = _wall_x(z)
    return _solid(_box(cx, y, z, sx, sy, sz))


def _oval_through_minus_x(y, z, length, height):
    """A stadium-shaped probe (long along Y) right through the -X wall."""
    x0 = -L.RIM.sx / 2 - 1.0
    face = Plane.YZ.offset(x0) * Pos(y, z) * SlotCenterToCenter(length - height, height)
    return extrude(face, amount=base.CAVITY_MIN_X - x0 + 0.5)


def test_the_cord_port_is_an_oval_on_the_inlet_that_a_c7_end_passes():
    z = params.FLOOR + m.CHARGER.inlet_center_z
    c7 = m.CORD_END                   # a figure-of-8 end: two round lobes
    assert _clear(_oval_through_minus_x(0, z, c7.width, c7.height))
    assert _clear(_oval_through_minus_x(0, z, base.CORD_W - 0.1, base.CORD_H - 0.1))
    # rounded ends: the corner of the port's bounding rectangle is still wall
    cy, cz = base.CORD_W / 2 - 0.3, z + base.CORD_H / 2 - 0.3
    assert not _clear(_through_minus_x(cy, cz, 0.2, 0.2))
    assert not _clear(_through_minus_x(0, z, base.CORD_W + 0.5, base.CORD_H + 0.5))


def test_the_cord_port_sill_clears_the_groove():
    """Spec: both kinds of wall port sit wholly above the colour groove --
    the sill must leave at least half a millimetre of solid wall above the
    groove's top flank."""
    z0 = params.BAND_H + base.GROOVE_UP
    z1 = base.CORD_Z0
    assert z1 - z0 >= 0.5 - 1e-9
    assert _wall_solid(0, (z0 + z1) / 2, base.CORD_W - 0.4, z1 - z0 - 0.2)


def test_two_oval_escape_ports_flank_the_charger():
    assert base.ESCAPE_L >= base.ESCAPE_H     # stays a valid stadium
    for s in (-1, 1):
        y, z = s * base.ESCAPE_Y, base.ESCAPE_ZC
        core = _through_minus_x(y, z, base.ESCAPE_L - base.ESCAPE_H, base.ESCAPE_H - 0.1)
        assert _clear(core)
        # a rounded end: the rectangle's corner is still wall
        cx, cz = y + s * (base.ESCAPE_L / 2 - 0.3), z + base.ESCAPE_H / 2 - 0.3
        assert not _clear(_through_minus_x(cx, cz, 0.2, 0.2))
        assert base.ESCAPE_ZC - base.ESCAPE_H / 2 > params.BAND_H + base.GROOVE_UP
        # a full WALL of material remains from each end of the port outward:
        # toward the fence on the inboard end, the corner arc on the outboard
        y_margin = 0.3
        probe_sy = params.WALL - 2 * y_margin
        for direction in (-1, 1):
            end = y + direction * base.ESCAPE_L / 2
            probe_y = end + direction * (y_margin + probe_sy / 2)
            assert _wall_solid(probe_y, z, probe_sy, 0.4)


# --- floor features -------------------------------------------------------------

def test_tie_holes_go_through_the_floor_and_feet_are_shallow_recesses():
    assert len(base.TIE_HOLES) >= 12
    for x, y in base.TIE_HOLES:
        assert _clear(Pos(x, y, -0.5) * Cylinder(base.TIE_D / 2 - 0.05, params.FLOOR + 1.0, align=_MIN))
    for x, y in base.FOOT_CENTRES:
        assert _clear(Pos(x, y, 0.01) * Cylinder(base.FOOT_R - 0.05, base.FOOT_RECESS_D - 0.02, align=_MIN))
        assert _solid(Pos(x, y, base.FOOT_RECESS_D + 0.02) * Cylinder(base.FOOT_R - 0.05, params.FLOOR - base.FOOT_RECESS_D - 0.04, align=_MIN))


# --- hinge ------------------------------------------------------------------------

def test_the_hinge_pins_and_relief_are_in_the_base():
    for xs in H.STATIONS:
        a, b = xs - H.HOOK_W / 2, xs + H.HOOK_W / 2
        assert _solid(H.x_cylinder(H.PIN_R * 0.5, a, b))
        ring = H.x_cylinder(H.RELIEF_R - 0.05, a, b) - H.x_cylinder(H.PIN_R + 0.05, a - 1, b + 1)
        assert _clear(ring)


# --- printability -----------------------------------------------------------------

def test_no_ceiling_longer_than_a_bridge_but_the_hinge_pins():
    """Open-top-up, no supports anywhere: every steep downward face is a
    bridge of MAX_BRIDGE or less, except the hinge pins' flat undersides
    (base.LONG_BRIDGES), which span the wide hook gap between the cheeks."""
    pin_flat_z = H.AXIS_Z - H.PIN_FLAT * H.PIN_R
    pin_span = H.HOOK_W + 2 * H.SIDE_CLR + 1.0
    for f in steep_faces(_base()):
        c = f.center()
        on_pin = (abs(c.Z - pin_flat_z) < 1e-6
                  and min(abs(c.X - xs) for xs in H.STATIONS) < 1e-6)
        limit = pin_span if on_pin else MAX_BRIDGE
        assert span(f) <= limit + 1e-6, f"{span(f):.1f} mm ceiling at {c}"
