"""Base tests. Everything is measured on the built solid: faces, wires,
bounding boxes and probe intersections, never a restatement of a constant."""
import math

import pytest
from build123d import Align, Axis, Box, Cylinder, GeomType, Pos, fillet

from dock import base, params, tray
from dock import measurements as m

_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)
MAX_BRIDGE = 20.0   # a ceiling this short prints unsupported


# --- helpers: everything below reads the solid ------------------------------

def _slab(p, z, thick=0.2):
    """Horizontal cross-section of the part at height z."""
    probe = Pos(base.BASE_X / 2, 0, z) * Box(2 * base.BASE_X, 2 * base.BASE_Y,
                                             thick, align=_CTR)
    return p & probe


# A height clear of every wall opening: the cord port and the escape port
# stack up the whole -X end wall between them, so the only unbroken band
# left below the rebate is between the escape port's head and the ledge.
CLEAR_Z = (base.ESCAPE_Z1 + base.BASE_H - base.REBATE_D) / 2


def _band(off_in, off_out, z0, h):
    """An annular band hugging the cavity outline, from `off_in` to `off_out`
    outward of it.  Offsetting a rounded rectangle keeps the corner arc
    centres, so this follows the cavity wall exactly, corners included."""
    def ring(d, dz, dh):
        b = Box(base.CAVITY_X + 2 * d, base.CAVITY_Y + 2 * d, dh,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
        return Pos(0, 0, dz) * fillet(b.edges().filter_by(Axis.Z),
                                      base.CAVITY_R + d)
    return Pos(base.BASE_X / 2, 0, z0) * (ring(off_out, 0, h)
                                          - ring(off_in, -1, h + 2))


def _is_solid_in(probe, p):
    return abs((probe & p).volume - probe.volume) < 1e-3


def _is_clear_of(probe, p):
    """Nothing of `p` is inside `probe`.  Relative, not absolute: a point
    probe can be smaller than the absolute tolerance used elsewhere, and
    then an absolute test would pass however solid it was."""
    return (probe & p).volume < probe.volume * 1e-6


def _outer_at(p, z):
    """The part's outer outline at height `z`, on a hair-thin slab."""
    return _slab(p, z, 2e-3).bounding_box()


def _cavity_bbox(p):
    """The lower cavity opening, measured clear of the fence and the ports."""
    ring = _slab(p, CLEAR_Z)
    top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    inner = top.inner_wires()
    assert len(inner) == 1, f"expected one cavity opening, found {len(inner)}"
    return inner[0].bounding_box()


def _free_standing(p, z):
    """Everything standing clear of the shell in the slab at height `z`.

    The cavity floor carries the fence, so a slab down there is no longer
    two pieces.  The shell is the one piece that reaches the section's own
    outline; whatever is left stands free of the walls.  The section's
    outline, not the part's: inside the plinth band the outer wall is drawn
    in from the footprint, so the part's bounding box is the wrong ruler."""
    slab = _slab(p, z)
    outline = slab.bounding_box()

    def is_shell(s):
        return s.bounding_box().min.X <= outline.min.X + 1e-6

    solids = slab.solids()
    shell = [s for s in solids if is_shell(s)]
    free = [s for s in solids if not is_shell(s)]
    assert len(shell) == 1, f"expected one shell ring at z = {z:.1f}"
    assert free, f"nothing stands free of the walls at z = {z:.1f}"
    return free


def _fence_section(p):
    """The fence's cross-section at mid-fence height, standing free of the
    walls: the largest of the free-standing pieces down there."""
    return max(_free_standing(p, params.V1_FLOOR + base.FENCE_H / 2),
               key=lambda s: s.volume)


def _pocket_port_face_x(p):
    """X of the charger's port face, read off the fence cross-section."""
    fence = _fence_section(p)
    return max(f.center().X for f in fence.faces().filter_by(Axis.X)
               if f.normal_at().X < 0)


def _end_wall_holes(p, sign):
    """Bounding boxes of the holes in an end wall, lowest first.  `sign` is
    the wall's outward X normal: -1 for the cord/escape wall, +1 for the LED
    wall.

    Read off the wall's cavity face rather than its outer one.  The plinth
    splits each outer end face into a tapered band and the upright above it,
    and the cord port straddles that join, so outside there is no single
    face left to read the holes from.  The cavity face is one unbroken plane
    from the floor to the ledge, and a hole that shows up in it is a hole
    that went all the way through the wall -- which is what these tests are
    really after."""
    cav = _cavity_bbox(p)
    x = cav.min.X if sign < 0 else cav.max.X
    faces = [f for f in p.faces().filter_by(Axis.X)
             if f.normal_at().X * sign < 0 and abs(f.center().X - x) < 1e-6]
    assert len(faces) == 1, (
        f"expected one cavity face on the {sign:+d}X end wall, "
        f"found {len(faces)}")
    return sorted((w.bounding_box() for w in faces[0].inner_wires()),
                  key=lambda b: b.min.Z)


def _cord_and_escape_holes(p):
    """The two holes in the -X end wall: the cord port, then the escape port
    directly above it."""
    holes = _end_wall_holes(p, -1)
    assert len(holes) == 2, (
        "expected the cord port and the escape port in the -X end wall, "
        f"found {len(holes)}")
    return holes


def _ledge_faces(p):
    z = base.BASE_H - base.REBATE_D
    return [f for f in p.faces().filter_by(Axis.Z)
            if abs(f.center().Z - z) < 1e-6 and f.normal_at().Z > 0]


def _bottom_wires(p):
    return p.faces().sort_by(Axis.Z)[0].inner_wires()


def _xy_gap(a, b):
    """Shortest distance between two bounding boxes in the floor plane; 0 if
    they overlap."""
    dx = max(a.min.X - b.max.X, b.min.X - a.max.X, 0.0)
    dy = max(a.min.Y - b.max.Y, b.min.Y - a.max.Y, 0.0)
    return math.hypot(dx, dy)


# --- outer shell -------------------------------------------------------------

def test_outer_size_wraps_the_tray_with_fit_clearance():
    s = base.build_base().bounding_box().size
    assert abs(s.X - (tray.TRAY_X + 2 * (params.V1_WALL + params.CLR_FIT))) < 1e-6
    # Y is allowed to grow if the charger fence needs it; it must never shrink.
    assert s.Y >= tray.TRAY_Y + 2 * (params.V1_WALL + params.CLR_FIT) - 1e-6


def test_base_fits_the_bed():
    s = base.build_base().bounding_box().size
    assert s.X <= params.BED_X and s.Y <= params.BED_Y


def test_base_is_one_valid_solid_on_the_bed():
    p = base.build_base()
    assert p.is_valid and len(p.solids()) == 1
    bb = p.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert abs(bb.size.Z - base.BASE_H) < 1e-6


def test_outer_vertical_corners_are_rounded():
    p = base.build_base()
    cyl = [f for f in p.faces()
           if f.geom_type == GeomType.CYLINDER
           and abs(f.radius - params.V1_CORNER_R) < 1e-6]
    assert len(cyl) >= 4


def test_bottom_outer_edge_is_chamfered_not_filleted():
    """Downward edges get a chamfer: the bed face is CHAMFER in from the
    plinth's own outline all round -- from the top of the chamfer, not from
    the part's footprint, which the plinth has already stepped away from --
    and the foot recesses stay inside it.  The flats are at 45 degrees,
    which is what makes it a chamfer and not a fillet."""
    p = base.build_base()
    bottom = p.faces().sort_by(Axis.Z)[0]
    fb = bottom.bounding_box().size
    plinth = _outer_at(p, params.CHAMFER).size
    assert abs(fb.X - (plinth.X - 2 * params.CHAMFER)) < 1e-3
    assert abs(fb.Y - (plinth.Y - 2 * params.CHAMFER)) < 1e-3
    assert len(bottom.inner_wires()) == len(base.TIE_GRID) + 4
    flats = [f for f in p.faces()
             if f.geom_type == GeomType.PLANE
             and abs(f.center().Z - params.CHAMFER / 2) < 1e-6
             and abs(math.degrees(math.acos(min(1.0, abs(f.normal_at().Z))))
                     - 45.0) < 1e-6]
    assert len(flats) == 4, "no 45 degree chamfer flats round the bed face"


def test_base_is_tall_enough_for_charger_cable_room_and_tray():
    p = base.build_base()
    h = p.bounding_box().size.Z
    assert h >= params.V1_FLOOR + m.CHARGER.height + base.CABLE_ROOM + tray.TRAY_H - 1e-6


# --- plinth ------------------------------------------------------------------

def test_the_plinth_steps_the_lower_walls_in_toward_the_bed():
    """The bottom PLINTH_H of the outer wall leans inward toward the bed, the
    way the Trek CHRGtime's does: PLINTH_INSET off every face by the top of
    the bottom chamfer, back to full size by PLINTH_H, and full size all the
    way up from there.  Measured on the solid at three heights."""
    p = base.build_base()
    full = p.bounding_box().size
    low = _outer_at(p, params.CHAMFER).size
    assert abs(low.X - (full.X - 2 * base.PLINTH_INSET)) < 1e-3
    assert abs(low.Y - (full.Y - 2 * base.PLINTH_INSET)) < 1e-3
    for z in (base.PLINTH_H + 1.0, base.BASE_H - 1.0):
        s = _outer_at(p, z).size
        assert abs(s.X - full.X) < 1e-6 and abs(s.Y - full.Y) < 1e-6, z


def test_the_step_in_happens_only_in_the_plinth_band():
    """A skin hugging the inside of the nominal footprint is empty all the
    way up the plinth and solid everywhere above it: the taper proved by
    where the wall is and is not, rather than by reading its faces."""
    p = base.build_base()
    bb = p.bounding_box()

    def skin(z0, z1):
        return Pos(base.BASE_X / 2, bb.max.Y - 0.05, (z0 + z1) / 2) * Box(
            40.0, 0.08, z1 - z0, align=_CTR)

    assert (skin(0.0, base.PLINTH_H - 0.5) & p).volume < 1e-3, (
        "the outer wall still reaches the full footprint down in the plinth")
    above = skin(base.PLINTH_H + 1.0, base.BASE_H - base.NOTCH_D)
    assert _is_solid_in(above, p), (
        "the wall does not come back out to the footprint above the plinth")


def test_the_plinth_leaves_a_full_wall_at_its_thinnest():
    """The shell below the rebate is 2*WALL thick and the plinth takes
    PLINTH_INSET off it, so at the top of the bottom chamfer -- the thinnest
    the plinth ever gets -- a full WALL of material is still there, corners
    included.  Measured as a band hugging the cavity outline: solid out to
    WALL, void a hair beyond it."""
    p = base.build_base()
    z, eps = params.CHAMFER, 5e-4
    assert _is_solid_in(_band(eps, params.V1_WALL - eps, z, 2e-3), p), (
        "the plinth eats into the wall somewhere round the band")
    beyond = _band(params.V1_WALL + 0.05, params.V1_WALL + 0.15, z, 2e-3)
    assert _is_clear_of(beyond, p), (
        "the wall is not stepped in down there at all")


def test_plinth_wall_thickness_on_every_side_and_through_a_corner():
    """The same thing read side by side, so a failure says which wall: the
    outer face at the top of the chamfer against the cavity face, on all
    four sides, and then out along each corner's diagonal, where the taper
    runs on a cone rather than a plane."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    out = _outer_at(p, params.CHAMFER)
    sides = {"-X": cav.min.X - out.min.X, "+X": out.max.X - cav.max.X,
             "-Y": cav.min.Y - out.min.Y, "+Y": out.max.Y - cav.max.Y}
    for name, t in sides.items():
        assert t >= params.V1_WALL - 0.05, f"{name} wall is only {t:.3f} mm"
    # Out of each corner arc's centre along the diagonal: material half a
    # wall out past the cavity arc, and none of it a hair past a full wall.
    cr, u = base.CAVITY_R, math.sqrt(0.5)
    for cx, sx in ((cav.min.X + cr, -1), (cav.max.X - cr, +1)):
        for cy, sy in ((cav.min.Y + cr, -1), (cav.max.Y - cr, +1)):
            def probe(d):
                return Pos(cx + sx * (cr + d) * u, cy + sy * (cr + d) * u,
                           params.CHAMFER + 1e-3) * Box(0.05, 0.05, 2e-3,
                                                        align=_CTR)
            assert _is_solid_in(probe(params.V1_WALL / 2), p), ("corner", cx, cy)
            assert _is_clear_of(probe(params.V1_WALL + 0.1), p), ("corner", cx, cy)


def test_the_plinth_taper_prints_unsupported():
    """The taper faces down and out, so it is an overhang -- but a shallow
    one: PLINTH_INSET over the PLINTH_H it has, less the chamfer it starts
    above.  Every downward face in the band is at that one angle, four walls
    and four corners, and nowhere near the 45 degrees this part is held to."""
    p = base.build_base()
    want = math.degrees(math.atan2(base.PLINTH_INSET,
                                   base.PLINTH_H - params.CHAMFER))
    faces = [f for f in p.faces()
             if f.normal_at().Z < -1e-6
             and params.CHAMFER + 1e-6 < f.center().Z < base.PLINTH_H - 1e-6]
    assert len(faces) == 8, (
        f"expected four taper walls and four taper corners, got {len(faces)}")
    for f in faces:
        got = math.degrees(math.asin(min(1.0, -f.normal_at().Z)))
        assert abs(got - want) < 1e-6, f"{got:.2f} deg at {f.center()}"
    assert want < 45.0 - 1e-6, f"the taper overhangs {want:.1f} deg"
    assert abs(want - base.PLINTH_TAPER_DEG) < 1e-9


def test_foot_recesses_stay_inside_the_plinth_bed_face():
    """The plinth shrinks the bed face, but FOOT_INSET is measured from the
    nominal footprint, so the feet have to still land wholly on it.  They
    are inner wires of that face -- a recess that broke its outline would
    not be one -- with room to spare on every side."""
    p = base.build_base()
    bottom = p.faces().sort_by(Axis.Z)[0]
    bed = bottom.bounding_box()
    feet = [w.bounding_box() for w in bottom.inner_wires()
            if abs(w.bounding_box().size.X - 2 * base.FOOT_R) < 1e-6]
    assert len(feet) == 4
    for f in feet:
        for margin in (f.min.X - bed.min.X, bed.max.X - f.max.X,
                       f.min.Y - bed.min.Y, bed.max.Y - f.max.Y):
            assert margin >= 2.0, (
                f"a foot recess is {margin:.2f} mm from the bed edge")


# --- rebate ------------------------------------------------------------------

def test_rebate_opening_matches_the_tray_plus_fit_clearance():
    """The ledge the tray lands on is bounded by the rebate opening."""
    p = base.build_base()
    ledge = _ledge_faces(p)
    assert ledge, "no horizontal ledge face at the bottom of the rebate"
    xs = [v for f in ledge for v in (f.bounding_box().min.X, f.bounding_box().max.X)]
    ys = [v for f in ledge for v in (f.bounding_box().min.Y, f.bounding_box().max.Y)]
    assert abs((max(xs) - min(xs)) - (tray.TRAY_X + 2 * params.CLR_FIT)) < 1e-6
    assert abs((max(ys) - min(ys)) - (tray.TRAY_Y + 2 * params.CLR_FIT)) < 1e-6


def test_rebate_is_tray_deep_so_the_tray_sits_flush():
    p = base.build_base()
    ledge_z = min(f.center().Z for f in _ledge_faces(p))
    assert abs((p.bounding_box().max.Z - ledge_z) - tray.TRAY_H) < 1e-6


def test_tray_seats_in_the_rebate_without_interference():
    p = base.build_base()
    seated = base.tray_seat() * tray.build_tray()
    assert (seated & p).volume < 1e-3
    assert abs(seated.bounding_box().max.Z - p.bounding_box().max.Z) < 1e-6


def test_the_ledge_is_full_width_all_round():
    """A LEDGE_W-wide band hugging the cavity wall, the whole way round and
    through the corners, is solid material just below the ledge and open
    rebate just above it.  That is the shelf, measured, not its bbox."""
    p = base.build_base()
    z = base.BASE_H - base.REBATE_D
    eps = 5e-4                                  # proves >= LEDGE_W - 1e-3
    below = _band(eps, base.LEDGE_W - eps, z - 0.3, 0.3)
    assert _is_solid_in(below, p), "the shelf is not full width all round"
    above = _band(eps, base.LEDGE_W - eps, z, 0.3)
    assert (above & p).volume < 1e-3, "the shelf is buried under the rim"


def test_the_tray_lands_flat_on_the_ledge_all_round():
    """The tray's bottom outer edge is chamfered, so only the inner part of
    the shelf sees flat-on-flat contact.  At least 1 mm of it does, all the
    way round -- measured against the seated tray, not against BEARING_W."""
    p = base.build_base()
    seated = base.tray_seat() * tray.build_tray()
    z = base.BASE_H - base.REBATE_D
    contact = _band(5e-3, 1.005, z, 0.3)
    assert _is_solid_in(contact, seated), "less than 1 mm of flat bearing"
    assert base.BEARING_W >= 1.0
    assert abs(base.BEARING_W
               - (base.LEDGE_W - params.CLR_FIT - params.CHAMFER)) < 1e-9


# --- charger fence -----------------------------------------------------------

def test_fence_stands_inside_the_cavity_with_clearance_each_side():
    p = base.build_base()
    cav = _cavity_bbox(p)
    fence = _fence_section(p).bounding_box()
    assert fence.min.X > cav.min.X and fence.max.X < cav.max.X
    # Backed onto the -X wall: the U's side walls stop a hair (CLR_FIT)
    # short of it.  That gap is a seam, not a clearance -- nothing seats in
    # it, and it is there so the U stays a solid of its own for these tests
    # to find.  The slicer fuses it back into the wall.
    assert fence.min.X - cav.min.X <= params.CLR_FIT + 1e-6
    assert fence.min.Y - cav.min.Y >= 2.0
    assert cav.max.Y - fence.max.Y >= 2.0


def test_base_y_is_wide_enough_for_the_fence_it_carries():
    """Measured on the solid: BASE_Y covers the fence plus FENCE_CLEAR_Y each
    side plus the two 2*WALL side walls, so a remeasured, wider charger grows
    the base instead of jamming."""
    p = base.build_base()
    fence = _fence_section(p).bounding_box()
    need = fence.size.Y + 2 * base.FENCE_CLEAR_Y + 4 * params.V1_WALL
    assert p.bounding_box().size.Y >= need - 1e-6


def test_pocket_holds_the_charger_with_fit_clearance():
    """A charger-sized block dropped into the pocket touches nothing, and the
    same block grown by the fit clearance still does."""
    p = base.build_base()
    for grow in (0.0, 2 * params.CLR_FIT - 0.01):
        probe = Pos(base.FENCE_CX, 0, params.V1_FLOOR) * Box(
            m.CHARGER.port_to_inlet + grow,
            m.CHARGER.port_face_width + grow,
            m.CHARGER.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (probe & p).volume < 1e-3, grow
    # ... and the fence really does hold it: a U, three walls round the
    # charger, with the cavity's own end wall closing the fourth side.
    sect = _fence_section(p).bounding_box()
    assert sect.size.X >= m.CHARGER.port_to_inlet + params.V1_WALL - 1e-6
    assert sect.size.Y >= m.CHARGER.port_face_width + 2 * params.V1_WALL - 1e-6
    # Open at -X: a bar laid down the pocket's centre line from the cavity's
    # end wall to the charger's port face meets nothing at fence height.
    cav = _cavity_bbox(p)
    back = Pos(cav.min.X, 0, params.V1_FLOOR + base.FENCE_H / 2) * Box(
        _pocket_port_face_x(p) - cav.min.X - 0.02, 20.0, base.FENCE_H - 0.02,
        align=(Align.MIN, Align.CENTER, Align.CENTER))
    assert (back & p).volume < 1e-3, "the fence still has a -X wall"


def test_room_in_front_of_the_ports_for_six_plugs():
    """Port room is everything from the charger's port face out to the +X
    cavity wall -- the charger is at the far end now, so that is most of the
    cavity.  PORT_PLUG_ROOM_MIN is only the floor under it."""
    p = base.build_base()
    free = _cavity_bbox(p).max.X - _pocket_port_face_x(p)
    assert free >= base.PORT_PLUG_ROOM_MIN - 1e-6, f"only {free:.1f} mm"
    assert abs(free - base.PORT_PLUG_ROOM) < 1e-6


def test_the_charger_backs_onto_the_minus_x_cavity_wall():
    """The CHRGtime stands its supply's back against the end wall, so the
    mains cord plugs in from outside, through the wall, straight into the
    inlet.  Measured on the solid: between that wall and the fence's +X wall
    there is the charger and the fit clearance, and nothing else -- no cord
    room behind it to fall into."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    run = _pocket_port_face_x(p) - cav.min.X
    slide = run - m.CHARGER.port_to_inlet
    assert slide >= 0, f"the charger does not fit: {run:.2f} mm"
    # All the slack there is, and it is not cord room: POCKET_BACK_SLACK for
    # whatever stands proud of the charger's back face, plus the pocket's
    # own fit clearance at each end of its length.
    allowed = base.POCKET_BACK_SLACK + 2 * params.CLR_FIT
    assert slide <= allowed + 1e-6, f"{slide:.2f} mm of slide"
    # pushed right back against the wall it still touches nothing
    probe = Pos(cav.min.X, 0, params.V1_FLOOR) * Box(
        m.CHARGER.port_to_inlet, m.CHARGER.port_face_width, m.CHARGER.height,
        align=(Align.MIN, Align.CENTER, Align.MIN))
    assert (probe & p).volume < 1e-3


# --- wall openings -----------------------------------------------------------

def test_cord_port_is_a_closed_hole_in_the_minus_x_wall_on_the_inlet():
    """A rectangular through-hole in the -X end wall, centred on the inlet in
    Y and spanning its centre height in Z -- not a notch open to the top.  It
    is the lower of that wall's two holes; the escape port sits above it."""
    p = base.build_base()
    bb, _ = _cord_and_escape_holes(p)
    assert abs(bb.size.Y - base.CORD_W) < 1e-6
    assert abs(bb.size.Z - base.CORD_H) < 1e-6
    assert abs(bb.center().Y) < 1e-6
    assert bb.min.Z < params.V1_FLOOR + m.CHARGER.inlet_center_z < bb.max.Z
    # ... and at full width there, not pinched down near either edge of the
    # rectangle: a bar across the whole opening at the inlet's centre height
    # passes through the wall.  A taller charger walks its inlet toward the
    # top of the opening, and this is what notices.
    inlet_z = params.V1_FLOOR + m.CHARGER.inlet_center_z
    span = Pos(-1, 0, inlet_z) * Box(
        2 * params.V1_WALL + 2, base.CORD_W - 0.02, 0.4,
        align=(Align.MIN, Align.CENTER, Align.CENTER))
    assert (span & p).volume < 1e-3, "the cord port does not reach the inlet"
    # closed: it stops well below the rebate ledge
    assert bb.max.Z <= base.BASE_H - base.REBATE_D - 1e-6
    # ... and it really goes through: a plug-sized bar passes from outside in
    bar = Pos(-1, 0, bb.min.Z + 0.01) * Box(
        2 * params.V1_WALL + 1, base.CORD_W - 0.02, base.CORD_H - 0.02,
        align=(Align.MIN, Align.CENTER, Align.MIN))
    assert (bar & p).volume < 1e-3


def test_the_moulded_cord_end_reaches_the_inlet_through_the_wall():
    """The charger's inlet face is right behind the -X wall, so the cord
    plugs in from outside: a block the size of CORD_END, held at the inlet's
    own centre height and ending on the pocket's back face, comes in from
    outside the dock, through the wall and up to the inlet, touching nothing.
    Nothing has to lift it or tilt it."""
    p = base.build_base()
    end = m.CORD_END
    # the pocket's back face: the cavity's own end wall, plus the slack
    # left for whatever stands proud of the charger's back
    back = _cavity_bbox(p).min.X + base.POCKET_BACK_SLACK
    probe = Pos(back, 0, params.V1_FLOOR + m.CHARGER.inlet_center_z) * Box(
        end.length, end.width, end.height,
        align=(Align.MAX, Align.CENTER, Align.CENTER))
    bb = probe.bounding_box()
    assert bb.min.X < 0, "the cord end does not reach outside the dock"
    assert bb.max.X > 2 * params.V1_WALL, "it does not clear the wall"
    assert abs(bb.max.X - base.POCKET_MIN_X) < 1e-6
    assert (probe & p).volume < 1e-3


def test_cord_port_is_a_plain_rectangle_needing_supports():
    """CORD_W is well past MAX_BRIDGE, so the port's ceiling is a plain flat
    rectangle that cannot print unsupported -- it is the one ceiling in
    SUPPORTED_CEILINGS, printed with supports rather than dodged with a
    peaked roof.  Measured on the solid."""
    p = base.build_base()
    assert base.CORD_W > MAX_BRIDGE

    # the opening itself: CORD_W x CORD_H, nothing more
    bb, _ = _cord_and_escape_holes(p)
    assert abs(bb.size.Y - base.CORD_W) < 1e-6
    assert abs(bb.size.Z - base.CORD_H) < 1e-6

    # the ceiling is a single flat downward face spanning the full CORD_W,
    # at the top of the opening
    ceiling_z = base.CORD_Z0 + base.CORD_H
    ceiling = [f for f in p.faces().filter_by(Axis.Z)
               if f.normal_at().Z < 0
               and abs(f.center().Z - ceiling_z) < 1e-6
               and 0 <= f.center().X <= 2 * params.V1_WALL
               and abs(f.center().Y) < base.CORD_W / 2 - 1e-3]
    assert len(ceiling) == 1, f"expected one flat ceiling face, got {len(ceiling)}"
    span = ceiling[0].bounding_box().size.Y
    assert abs(span - base.CORD_W) < 1e-6
    assert span > MAX_BRIDGE, "a self-supporting ceiling would not need this test"

    # the moulded cord end still reaches the inlet through it, centred and
    # touching nothing
    end = m.CORD_END
    back = _cavity_bbox(p).min.X + base.POCKET_BACK_SLACK
    probe = Pos(back, 0, params.V1_FLOOR + m.CHARGER.inlet_center_z) * Box(
        end.length, end.width, end.height,
        align=(Align.MAX, Align.CENTER, Align.CENTER))
    assert (probe & p).volume < 1e-3


def test_the_rim_and_the_ledge_are_continuous_all_round():
    """Nothing but the two lift-out notches breaks the rim, and nothing at
    all breaks the shelf: one closed ring at every height below the notches,
    and across the notches the rim parts in exactly those two places."""
    p = base.build_base()
    z = base.BASE_H - base.REBATE_D
    for height, what in ((z - 0.2, "shelf"), (z + 0.2, "rim"),
                         (base.BASE_H - base.NOTCH_D - 0.2, "rim under the notches")):
        ring = _slab(p, height)
        assert len(ring.solids()) == 1, what
        top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
        assert len(top.inner_wires()) == 1, what
    across = _slab(p, base.BASE_H - 1.0).solids()
    assert len(across) == 2, (
        f"the rim should part at the two notches and nowhere else, "
        f"got {len(across)} pieces")
    # ... and the two pieces are the long side rails, one each side of Y = 0
    ys = sorted(s.center().Y for s in across)
    assert ys[0] < 0 < ys[1]


# --- lift-out notches ---------------------------------------------------------

def _notch_floors(p):
    """The two notch floors: upward faces at the bottom of the notches."""
    z = base.BASE_H - base.NOTCH_D
    return [f for f in p.faces().filter_by(Axis.Z)
            if f.normal_at().Z > 0 and abs(f.center().Z - z) < 1e-6]


def test_each_end_rim_has_a_finger_notch_for_lifting_the_tray():
    """A notch NOTCH_W wide and NOTCH_D deep is cut out of the rim at each
    end, centred on Y = 0: the rim there is void, and what is left below is
    a floor NOTCH_W wide less its two rounded corners."""
    p = base.build_base()
    floors = _notch_floors(p)
    assert len(floors) == 2, f"expected two notch floors, got {len(floors)}"
    for f in floors:
        bb = f.bounding_box()
        assert abs(bb.size.Y - (base.NOTCH_W - 2 * base.NOTCH_R)) < 1e-6
        assert abs(bb.size.X - params.V1_WALL) < 1e-6     # the rim's thickness
        assert abs(bb.center().Y) < 1e-6
    xs = sorted(f.center().X for f in floors)
    assert xs[0] < params.V1_WALL and xs[1] > base.BASE_X - params.V1_WALL
    # The rim itself is gone: full NOTCH_W wide above the rounded corners,
    # and right down to the floor between them.
    for cx in (params.V1_WALL / 2, base.BASE_X - params.V1_WALL / 2):
        for w, z0, h in (
                (base.NOTCH_W, base.NOTCH_R, base.NOTCH_D - base.NOTCH_R),
                (base.NOTCH_W - 2 * base.NOTCH_R, 0.0, base.NOTCH_D)):
            probe = Pos(cx, 0, base.BASE_H - base.NOTCH_D + z0 + 0.01) * Box(
                params.V1_WALL - 0.02, w - 0.02, h - 0.02,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
            assert (probe & p).volume < 1e-3, (cx, w)


def test_notch_bottom_corners_are_rounded():
    """Sharp inside corners in a 2.4 mm rim are where it splits; each notch
    turns into its floor on an R NOTCH_R arc."""
    p = base.build_base()
    z = base.BASE_H - base.NOTCH_D + base.NOTCH_R
    arcs = [f for f in p.faces()
            if f.geom_type == GeomType.CYLINDER
            and abs(f.radius - base.NOTCH_R) < 1e-6
            and abs(f.center().Z - z) < base.NOTCH_R]
    assert len(arcs) == 4, f"expected two rounded corners per notch, got {len(arcs)}"


def test_the_notches_clear_the_end_wall_openings():
    """The notches cut the rim only: every end-wall opening is still a closed
    hole, well below the notch floors -- the two stacked ports in the -X wall
    and, when the charger has an LED, its window in the +X wall."""
    p = base.build_base()
    floor_z = min(f.center().Z for f in _notch_floors(p))
    for sign, want in ((-1, 2), (+1, 1 if base.HAS_LED else 0)):
        holes = _end_wall_holes(p, sign)
        assert len(holes) == want, "an end-wall opening ran into its notch"
        assert all(h.max.Z < floor_z for h in holes)


@pytest.mark.skipif(not base.HAS_LED, reason="this charger has no status LED")
def test_led_window_is_outboard_of_port_one_in_the_plus_x_wall():
    p = base.build_base()
    outer = max((f for f in p.faces().filter_by(Axis.X) if f.normal_at().X > 0),
                key=lambda f: f.center().X)
    inner = outer.inner_wires()
    assert len(inner) == 1, "expected exactly one hole in the +X end wall"
    bb = inner[0].bounding_box()
    assert abs(bb.size.Y - base.LED_W) < 1e-6
    assert abs(bb.size.Z - base.LED_H) < 1e-6
    # wide in Y to catch the LED, short in Z because that is what bridges
    assert base.LED_W > base.LED_H and base.LED_W <= MAX_BRIDGE
    assert abs(bb.center().Z - (params.V1_FLOOR + m.CHARGER.height / 2)) < 1e-6
    # inside the pocket's Y span, and outboard of the first port
    fence = _fence_section(p).bounding_box()
    assert fence.min.Y < bb.center().Y < fence.max.Y
    port_one_y = base.POCKET_MIN_Y + m.CHARGER.port_face_margin
    assert bb.center().Y < port_one_y, "LED window is inboard of port 1"
    assert base.POCKET_MIN_Y <= bb.center().Y


# An LED shining down a long air gap lights the whole cavity instead of the
# window; keep the window within a hand's width of the LED itself.
MAX_LED_THROW = 45.0


@pytest.mark.skipif(not base.HAS_LED, reason="this charger has no status LED")
def test_led_window_is_close_enough_to_the_led_to_see_it():
    """Measured on the solid: the fence is placed from the +X side, so the
    charger's port face (which carries the LED) is near the +X end wall."""
    p = base.build_base()
    throw = p.bounding_box().max.X - _pocket_port_face_x(p)
    assert 0 < throw <= MAX_LED_THROW, f"LED window is {throw:.1f} mm from the port face"


@pytest.mark.skipif(base.HAS_LED, reason="this charger has a status LED")
def test_no_led_window_when_the_charger_has_no_led():
    """A charger with no LED gets no window cut for one: the +X end wall is
    blind, and the only openings left in the part are the two in the -X wall
    and the two rim notches."""
    p = base.build_base()
    assert not _end_wall_holes(p, +1)
    assert len(_end_wall_holes(p, -1)) == 2


def test_escape_port_sits_directly_above_the_cord_port():
    """The CHRGtime puts the device-cable escape directly above the AC cord
    port in the same wall.  Measured on the solid: two holes in the -X end
    wall, on the same centre line, the escape port the upper one."""
    p = base.build_base()
    cord, escape = _cord_and_escape_holes(p)
    assert abs(escape.size.Y - base.ESCAPE_W) < 1e-6
    assert abs(escape.size.Z - base.ESCAPE_H) < 1e-6
    assert abs(escape.center().Y) < 1e-6
    assert abs(escape.center().Y - cord.center().Y) < 1e-6
    # a ligament of material between the two: the sill sits at least the
    # 1 mm the design asks for above the cord port's flat top
    assert escape.min.Z - cord.max.Z >= 1.0 - 1e-6
    # sized for a device-end plug: a USB-C overmold with slack either side
    assert escape.size.Y >= params.USB_C_PLUG.width + 4.0
    assert escape.size.Z >= params.USB_C_PLUG.height
    # and its flat ceiling is a bridge the printer can cross
    assert escape.size.Y <= MAX_BRIDGE


def test_escape_port_stays_clear_of_the_rebate_ledge():
    """It is a closed hole, not a notch: ESCAPE_LEDGE_GAP_MIN of wall is left
    between its head and the shelf the tray lands on."""
    p = base.build_base()
    _, escape = _cord_and_escape_holes(p)
    ledge_z = min(f.center().Z for f in _ledge_faces(p))
    gap = ledge_z - escape.max.Z
    assert gap >= base.ESCAPE_LEDGE_GAP_MIN - 1e-6, f"only {gap:.2f} mm"


def test_escape_port_goes_right_through_into_the_cavity():
    """A bar the size of the opening passes from outside the -X wall into
    the cavity, touching nothing -- including the cord port below it."""
    p = base.build_base()
    _, escape = _cord_and_escape_holes(p)
    bar = Pos(-1, escape.center().Y, escape.min.Z + 0.01) * Box(
        2 * params.V1_WALL + 2, escape.size.Y - 0.02, escape.size.Z - 0.02,
        align=(Align.MIN, Align.CENTER, Align.MIN))
    assert bar.bounding_box().max.X > 2 * params.V1_WALL
    assert (bar & p).volume < 1e-3


def test_the_long_walls_carry_no_openings():
    """The escape port used to break the rear (-Y) wall under the tray's
    spare bay; now that it is in the -X end wall, both long walls are whole."""
    p = base.build_base()
    for sign in (-1, +1):
        face = (max if sign > 0 else min)(
            (f for f in p.faces().filter_by(Axis.Y)
             if f.normal_at().Y * sign > 0), key=lambda f: f.center().Y)
        assert not face.inner_wires(), f"a hole is left in the {sign:+d}Y wall"


# --- charger ports ------------------------------------------------------------

def test_a_plug_in_every_charger_port_clears_the_base():
    """A USB-A overmold -- the largest of the plug envelopes, used for all
    six ports -- butted against the charger's port face at each port centre,
    at the charger's mid height, touches nothing in the base: not the fence,
    not a wall.  The Anker A2154 ships with its own silicone cable-management
    block, so nothing printed has to stand clear of a cable here beyond the
    plug itself.

    Deliberately plug against base only, never plug against plug: on a port
    pitch narrower than an overmold the plugs foul each other, which is the
    charger's problem and the cable set's, not the dock's."""
    p = base.build_base()
    assert len(base.PORT_YS) == 6
    port_x = _pocket_port_face_x(p)
    plug = params.USB_A_PLUG
    for y in base.PORT_YS:
        probe = Pos(port_x, y, params.V1_FLOOR + m.CHARGER.height / 2) * Box(
            plug.length, plug.width, plug.height,
            align=(Align.MIN, Align.CENTER, Align.CENTER))
        assert (probe & p).volume < 1e-3, f"plug at y = {y:.1f} fouls the base"


def test_walls_below_the_rebate_are_two_walls_thick():
    """Measured on the solid: at mid-cavity height the shell is 2*WALL of
    solid material, and nothing beyond it."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    z = CLEAR_Z
    t = 2 * params.V1_WALL

    # CLEAR_Z sits in a 1 mm band between the escape port's head and the
    # ledge, so the probe has to be short enough to stay inside it.
    def probe(cx, cy, sx, sy):
        return Pos(cx, cy, z) * Box(sx, sy, 0.8, align=_CTR)

    y = cav.max.Y + t / 2                      # +Y wall, clear of every cutout
    solid = probe(base.BASE_X / 2 - 40, y, 20, t - 0.02)
    assert abs((solid & p).volume - solid.volume) < 1e-3
    void = probe(base.BASE_X / 2 - 40, cav.max.Y + t + 0.25, 20, 0.4)
    assert (void & p).volume < 1e-3


# --- floor -------------------------------------------------------------------

def test_four_foot_recesses_under_the_corners():
    p = base.build_base()
    feet = [w for w in _bottom_wires(p)
            if abs(w.bounding_box().size.X - 2 * base.FOOT_R) < 1e-6]
    assert len(feet) == 4
    xs = sorted({round(w.bounding_box().center().X, 3) for w in feet})
    ys = sorted({round(w.bounding_box().center().Y, 3) for w in feet})
    assert len(xs) == 2 and len(ys) == 2
    assert abs(ys[0] + ys[1]) < 1e-6           # symmetric about Y = 0
    assert abs(xs[0] - base.FOOT_INSET) < 1e-6
    assert abs(xs[1] - (base.BASE_X - base.FOOT_INSET)) < 1e-6


def test_foot_recesses_are_shallow_enough_to_leave_floor():
    p = base.build_base()
    ceil = [f for f in p.faces().filter_by(Axis.Z)
            if f.normal_at().Z < 0 and abs(f.center().Z - base.FOOT_RECESS_D) < 1e-6]
    assert len(ceil) == 4
    assert base.FOOT_RECESS_D < params.V1_FLOOR - 0.5


def test_tie_grid_holes_go_right_through_the_floor():
    p = base.build_base()
    assert len(_bottom_wires(p)) == len(base.TIE_GRID) + 4
    ties = [w for w in _bottom_wires(p)
            if abs(w.bounding_box().size.X - base.TIE_D) < 1e-6]
    assert len(ties) == len(base.TIE_GRID)
    seen = {(round(w.bounding_box().center().X, 3),
             round(w.bounding_box().center().Y, 3)) for w in ties}
    assert seen == {(round(x, 3), round(y, 3)) for x, y in base.TIE_GRID}
    # open to the cavity above: a pin through each hole meets nothing
    for x, y in base.TIE_GRID:
        pin = Pos(x, y, -1) * Cylinder(base.TIE_D / 2 - 0.01, params.V1_FLOOR + 2,
                                       align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (pin & p).volume < 1e-3, (x, y)


def test_tie_grid_sits_between_the_fence_and_the_plus_x_wall():
    """The free floor in front of the charger, the whole way out to the +X
    wall, carries the grid now that nothing stands on the floor to break it
    up.  Measured on the solid: every hole is clear of the fence and inside
    the cavity, and the columns span from just past the fence to just short
    of the +X wall."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    fence = _fence_section(p).bounding_box()
    assert base.TIE_GRID
    for x, y in base.TIE_GRID:
        assert x - base.TIE_D / 2 > fence.max.X
        assert x + base.TIE_D / 2 < cav.max.X
        assert cav.min.Y < y - base.TIE_D / 2 and y + base.TIE_D / 2 < cav.max.Y
    xs = {x for x, _ in base.TIE_GRID}
    assert min(xs) - (fence.max.X + base.TIE_MARGIN) < base.TIE_PITCH
    assert (cav.max.X - base.TIE_MARGIN) - max(xs) < base.TIE_PITCH


def test_tie_grid_is_on_a_regular_pitch():
    xs = sorted({round(x, 3) for x, _ in base.TIE_GRID})
    ys = sorted({round(y, 3) for _, y in base.TIE_GRID})
    assert len(xs) >= 2 and len(ys) >= 2
    for axis in (xs, ys):
        steps = {round(b - a, 3) for a, b in zip(axis, axis[1:])}
        assert steps == {base.TIE_PITCH}, steps


def test_tie_holes_clear_the_foot_recesses():
    """A hole breaking into a foot recess leaves 1 mm of floor and an
    unseatable foot; measured as disjoint wires on the bed face."""
    p = base.build_base()
    wires = _bottom_wires(p)
    for a in wires:
        for b in wires:
            if a is b:
                continue
            ba, bb = a.bounding_box(), b.bounding_box()
            gap = math.dist((ba.center().X, ba.center().Y),
                            (bb.center().X, bb.center().Y))
            assert gap > (ba.size.X + bb.size.X) / 2, (ba.center(), bb.center())


# --- printability ------------------------------------------------------------

def test_no_unsupported_ceilings():
    """Open-top-up.  Every downward ceiling steeper than 45 degrees has to
    span MAX_BRIDGE or less, with exactly one allowlisted exception: the
    cord port's flat ceiling (SUPPORTED_CEILINGS), identified here by where
    it is (the -X wall) and what it is (a CORD_W-wide face at
    CORD_Z0 + CORD_H) -- not by relaxing MAX_BRIDGE itself.  Everything else
    that bridges -- the escape port (ESCAPE_W), the LED window when there is
    one, and the four foot recesses -- still has to clear the same limit.
    The notch floors face up, not down."""
    p = base.build_base()
    bed_z = p.bounding_box().min.Z
    cord_ceiling_z = base.CORD_Z0 + base.CORD_H
    for f in p.faces():
        n = f.normal_at()
        if n.Z >= -1e-6 or abs(f.center().Z - bed_z) < 1e-6:
            continue
        overhang = math.degrees(math.asin(min(1.0, -n.Z)))
        if overhang <= 45.0 + 1e-6:
            continue
        s = f.bounding_box().size
        if (0 <= f.center().X <= 2 * params.V1_WALL
                and abs(f.center().Z - cord_ceiling_z) < 1e-6
                and abs(s.Y - base.CORD_W) < 1e-6):
            continue  # the one ceiling in base.SUPPORTED_CEILINGS
        assert max(s.X, s.Y) <= MAX_BRIDGE, (
            f"{overhang:.1f} deg ceiling spanning {max(s.X, s.Y):.1f} mm "
            f"at {f.center()}")
