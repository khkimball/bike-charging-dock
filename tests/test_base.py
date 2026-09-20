"""Base tests. Everything is measured on the built solid: faces, wires,
bounding boxes and probe intersections, never a restatement of a constant."""
import math

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


# A height clear of every wall opening: the cord port's peak now reaches
# above the escape port's sill, so the only unbroken band left below the
# rebate is between the escape port's head and the ledge.
CLEAR_Z = (base.ESCAPE_TOP + base.BASE_H - base.REBATE_D) / 2


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


def _cavity_bbox(p):
    """The lower cavity opening, measured clear of the fence and the ports."""
    ring = _slab(p, CLEAR_Z)
    top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    inner = top.inner_wires()
    assert len(inner) == 1, f"expected one cavity opening, found {len(inner)}"
    return inner[0].bounding_box()


def _fence_section(p):
    """The fence's cross-section at mid-fence height, standing free of the walls."""
    solids = _slab(p, params.FLOOR + base.FENCE_H / 2).solids()
    assert len(solids) == 2, f"fence should stand free of the walls, got {len(solids)}"
    return min(solids, key=lambda s: s.bounding_box().size.X)


def _pocket_port_face_x(p):
    """X of the charger's port face, read off the fence cross-section."""
    fence = _fence_section(p)
    return max(f.center().X for f in fence.faces().filter_by(Axis.X)
               if f.normal_at().X < 0)


def _pocket_inlet_face_x(p):
    fence = _fence_section(p)
    return min(f.center().X for f in fence.faces().filter_by(Axis.X)
               if f.normal_at().X > 0)


def _ledge_faces(p):
    z = base.BASE_H - base.REBATE_D
    return [f for f in p.faces().filter_by(Axis.Z)
            if abs(f.center().Z - z) < 1e-6 and f.normal_at().Z > 0]


def _bottom_wires(p):
    return p.faces().sort_by(Axis.Z)[0].inner_wires()


# --- outer shell -------------------------------------------------------------

def test_outer_size_wraps_the_tray_with_fit_clearance():
    s = base.build_base().bounding_box().size
    assert abs(s.X - (tray.TRAY_X + 2 * (params.WALL + params.CLR_FIT))) < 1e-6
    # Y is allowed to grow if the charger fence needs it; it must never shrink.
    assert s.Y >= tray.TRAY_Y + 2 * (params.WALL + params.CLR_FIT) - 1e-6


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
           and abs(f.radius - params.CORNER_R) < 1e-6]
    assert len(cyl) >= 4


def test_bottom_outer_edge_is_chamfered_not_filleted():
    """Downward edges get a chamfer: the bed face is CHAMFER in from the
    outer profile all round, and the foot recesses stay inside it."""
    p = base.build_base()
    bb = p.bounding_box().size
    bottom = p.faces().sort_by(Axis.Z)[0]
    fb = bottom.bounding_box().size
    assert abs(fb.X - (bb.X - 2 * params.CHAMFER)) < 1e-6
    assert abs(fb.Y - (bb.Y - 2 * params.CHAMFER)) < 1e-6
    assert len(bottom.inner_wires()) == len(base.TIE_GRID) + 4


def test_base_is_tall_enough_for_charger_cable_room_and_tray():
    p = base.build_base()
    h = p.bounding_box().size.Z
    assert h >= params.FLOOR + m.CHARGER.height + base.CABLE_ROOM + tray.TRAY_H - 1e-6


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
    assert fence.min.Y - cav.min.Y >= 2.0
    assert cav.max.Y - fence.max.Y >= 2.0


def test_base_y_is_wide_enough_for_the_fence_it_carries():
    """Measured on the solid: BASE_Y covers the fence plus FENCE_CLEAR_Y each
    side plus the two 2*WALL side walls, so a remeasured, wider charger grows
    the base instead of jamming."""
    p = base.build_base()
    fence = _fence_section(p).bounding_box()
    need = fence.size.Y + 2 * base.FENCE_CLEAR_Y + 4 * params.WALL
    assert p.bounding_box().size.Y >= need - 1e-6


def test_pocket_holds_the_charger_with_fit_clearance():
    """A charger-sized block dropped into the pocket touches nothing, and the
    same block grown by the fit clearance still does."""
    p = base.build_base()
    for grow in (0.0, 2 * params.CLR_FIT - 0.01):
        probe = Pos(base.FENCE_CX, 0, params.FLOOR) * Box(
            m.CHARGER.port_to_inlet + grow,
            m.CHARGER.port_face_width + grow,
            m.CHARGER.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (probe & p).volume < 1e-3, grow
    # ... and the fence really does surround it: the section is a ring, not a bar
    sect = _fence_section(p).bounding_box()
    assert sect.size.X >= m.CHARGER.port_to_inlet + 2 * params.WALL - 1e-6
    assert sect.size.Y >= m.CHARGER.port_face_width + 2 * params.WALL - 1e-6


def test_room_in_front_of_the_ports_for_six_plugs():
    p = base.build_base()
    free = _cavity_bbox(p).max.X - _pocket_port_face_x(p)
    assert free >= base.PORT_PLUG_ROOM_MIN - 1e-6, f"only {free:.1f} mm"


def test_room_behind_the_inlet_for_the_mains_cord():
    p = base.build_base()
    free = _pocket_inlet_face_x(p) - _cavity_bbox(p).min.X
    assert free >= base.INLET_PLUG_ROOM - 1e-6, f"only {free:.1f} mm"


# --- wall openings -----------------------------------------------------------

def test_cord_port_is_a_closed_hole_in_the_minus_x_wall_on_the_inlet():
    """A rectangular through-hole in the -X end wall, centred on the inlet in
    Y and spanning its centre height in Z -- not a notch open to the top."""
    p = base.build_base()
    outer = min((f for f in p.faces().filter_by(Axis.X) if f.normal_at().X < 0),
                key=lambda f: f.center().X)
    inner = outer.inner_wires()
    assert len(inner) == 1, "expected exactly one hole in the -X end wall"
    bb = inner[0].bounding_box()
    assert abs(bb.size.Y - base.CORD_W) < 1e-6
    assert abs(bb.size.Z - (base.CORD_H + base.CORD_W / 2)) < 1e-6
    assert abs(bb.center().Y) < 1e-6
    assert bb.min.Z < params.FLOOR + m.CHARGER.inlet_center_z < bb.max.Z
    # closed: it stops well below the rebate ledge
    assert bb.max.Z <= base.BASE_H - base.REBATE_D - 1e-6
    # ... and it really goes through: a plug-sized bar passes from outside in
    bar = Pos(-1, 0, bb.min.Z + 0.01) * Box(
        2 * params.WALL + 1, base.CORD_W - 0.02, base.CORD_H - 0.02,
        align=(Align.MIN, Align.CENTER, Align.MIN))
    assert (bar & p).volume < 1e-3


def test_the_moulded_cord_end_passes_through_the_cord_port():
    """The port is sized from the cord end that has to pass it, not from a
    round number: a block the size of CORD_END slides in through the -X wall
    and out into the cavity, touching nothing on the way."""
    p = base.build_base()
    end = m.CORD_END
    z0 = base.CORD_Z0 + (base.CORD_H - end.height) / 2
    probe = Pos(-5, 0, z0) * Box(end.length, end.width, end.height,
                                 align=(Align.MIN, Align.CENTER, Align.MIN))
    assert probe.bounding_box().min.X < 0 < 2 * params.WALL < probe.bounding_box().max.X
    assert (probe & p).volume < 1e-3


def test_cord_port_roof_is_a_self_supporting_peak():
    """CORD_W is well past the 20 mm bridge allowance, so the port's ceiling
    is not a bridge at all: two 45 degree planes meeting at a ridge over the
    port's centre line, measured on the solid."""
    p = base.build_base()
    roof = [f for f in p.faces()
            if 0 < f.center().X < 2 * params.WALL
            and f.center().Z > base.CORD_Z0 + base.CORD_H   # clear of the
            and abs(f.center().Y) < base.CORD_W             # bottom chamfer
            and abs(-f.normal_at().Z - math.sin(math.radians(45))) < 1e-6]
    assert len(roof) == 2, f"expected two 45 degree roof planes, got {len(roof)}"
    ys = sorted(f.center().Y for f in roof)
    assert ys[0] < 0 < ys[1], "the two planes should fall away either side"
    apex = max(f.bounding_box().max.Z for f in roof)
    assert abs(apex - (base.CORD_Z0 + base.CORD_H + base.CORD_W / 2)) < 1e-6
    # the ridge is a line, not a flat: no horizontal ceiling over the port
    flat = [f for f in p.faces().filter_by(Axis.Z)
            if f.normal_at().Z < 0
            and 0 < f.center().X < 2 * params.WALL
            and abs(f.center().Y) < base.CORD_W / 2]
    assert not flat, "the cord port still has a flat ceiling to bridge"


def test_the_rim_and_the_ledge_are_continuous_all_round():
    """Nothing breaks the rim or the shelf: one closed ring at each height."""
    p = base.build_base()
    z = base.BASE_H - base.REBATE_D
    for height, what in ((z - 0.2, "shelf"), (z + 0.2, "rim"),
                         (base.BASE_H - 1.0, "rim top")):
        ring = _slab(p, height)
        assert len(ring.solids()) == 1, what
        top = ring.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
        assert len(top.inner_wires()) == 1, what


def test_led_window_is_outboard_of_port_one_in_the_plus_x_wall():
    p = base.build_base()
    outer = max((f for f in p.faces().filter_by(Axis.X) if f.normal_at().X > 0),
                key=lambda f: f.center().X)
    inner = outer.inner_wires()
    assert len(inner) == 1, "expected exactly one hole in the +X end wall"
    bb = inner[0].bounding_box()
    assert abs(bb.size.Y - base.LED_W) < 1e-6 and abs(bb.size.Z - base.LED_W) < 1e-6
    assert abs(bb.center().Z - (params.FLOOR + m.CHARGER.height / 2)) < 1e-6
    # inside the pocket's Y span, and outboard of the first port
    fence = _fence_section(p).bounding_box()
    assert fence.min.Y < bb.center().Y < fence.max.Y
    port_one_y = base.POCKET_MIN_Y + m.CHARGER.port_face_margin
    assert bb.center().Y < port_one_y, "LED window is inboard of port 1"
    assert base.POCKET_MIN_Y <= bb.center().Y


# An LED shining down a long air gap lights the whole cavity instead of the
# window; keep the window within a hand's width of the LED itself.
MAX_LED_THROW = 45.0


def test_led_window_is_close_enough_to_the_led_to_see_it():
    """Measured on the solid: the fence is placed from the +X side, so the
    charger's port face (which carries the LED) is near the +X end wall."""
    p = base.build_base()
    throw = p.bounding_box().max.X - _pocket_port_face_x(p)
    assert 0 < throw <= MAX_LED_THROW, f"LED window is {throw:.1f} mm from the port face"


def test_escape_port_is_in_the_rear_wall_below_the_ledge():
    p = base.build_base()
    rear = min((f for f in p.faces().filter_by(Axis.Y) if f.normal_at().Y < 0),
               key=lambda f: f.center().Y)
    inner = rear.inner_wires()
    assert len(inner) == 1
    bb = inner[0].bounding_box()
    assert abs(bb.size.Z - base.ESCAPE_H) < 1e-6
    assert abs(bb.size.X - (params.USB_A_PLUG.width + 4)) < 1e-6
    ledge_z = min(f.center().Z for f in _ledge_faces(p))
    assert bb.max.Z <= ledge_z - params.WALL + 1e-6
    # centred on the spare bay, in base coordinates
    x0, _, w, _ = tray.RIGHT_BAYS["spare"]
    seat_x = base.tray_seat().position.X
    assert abs(bb.center().X - (seat_x + x0 + w / 2)) < 1e-6


def test_walls_below_the_rebate_are_two_walls_thick():
    """Measured on the solid: at mid-cavity height the shell is 2*WALL of
    solid material, and nothing beyond it."""
    p = base.build_base()
    cav = _cavity_bbox(p)
    z = CLEAR_Z
    t = 2 * params.WALL

    def probe(cx, cy, sx, sy):
        return Pos(cx, cy, z) * Box(sx, sy, 2.0, align=_CTR)

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
    assert base.FOOT_RECESS_D < params.FLOOR - 0.5


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
        pin = Pos(x, y, -1) * Cylinder(base.TIE_D / 2 - 0.01, params.FLOOR + 2,
                                       align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (pin & p).volume < 1e-3, (x, y)


def test_tie_grid_sits_between_the_fence_and_the_plus_x_wall():
    p = base.build_base()
    cav = _cavity_bbox(p)
    fence = _fence_section(p).bounding_box()
    assert base.TIE_GRID
    for x, y in base.TIE_GRID:
        assert x - base.TIE_D / 2 > fence.max.X
        assert x + base.TIE_D / 2 < cav.max.X
        assert cav.min.Y < y - base.TIE_D / 2 and y + base.TIE_D / 2 < cav.max.Y


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
    """Open-top-up: the only ceilings are the escape port, the LED window and
    the four foot recesses, all short bridges."""
    p = base.build_base()
    bed_z = p.bounding_box().min.Z
    for f in p.faces():
        n = f.normal_at()
        if n.Z >= -1e-6 or abs(f.center().Z - bed_z) < 1e-6:
            continue
        overhang = math.degrees(math.asin(min(1.0, -n.Z)))
        if overhang <= 45.0 + 1e-6:
            continue
        s = f.bounding_box().size
        assert max(s.X, s.Y) <= MAX_BRIDGE, (
            f"{overhang:.1f} deg ceiling spanning {max(s.X, s.Y):.1f} mm "
            f"at {f.center()}")
