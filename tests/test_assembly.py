"""Assembly checks: cross-part fit that isn't already covered in
test_base.py (tray vs base) or test_lid.py (lid vs base).  Everything below
is measured on the built and seated solids, never restated from constants.

Seating: `base.tray_seat()` places the tray in the base's rebate;
`lid.lid_seat()` flips the lid onto the base.  Device envelopes are built
from `measurements.py` slabs, positioned at their bay's `tray.ROAM_BAY` /
`tray.RIGHT_BAYS` footprint inset by `CLR_BAY` and pushed to the end of the
bay away from its cable cutout (ROAM against the +Y wall, the right-column
devices against the partition at -X) -- matching how `tray.py` reserves the
cutout at the opposite end.
"""
import sys
from pathlib import Path

from build123d import Align, Axis, Box, Pos

from dock import base, lid, tray
from dock import measurements as m
from dock import params as P

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_all import PARTS  # noqa: E402  (needs the path insert above)

_MIN = (Align.MIN, Align.MIN, Align.MIN)
# The lid lands on the base rim and the tray is flush with it, so anything
# loose in the tray has to finish clear of the lid ceiling by this much.
MIN_STACK_GAP = 0.4


def _seated_tray():
    return base.tray_seat() * tray.build_tray()


def _seated_lid():
    return lid.lid_seat() * lid.build_lid()


def _device_box(x0, y0, w, l, length, width, thickness, *, along_x, near_min):
    """A device-sized box in tray-local coordinates, at its bay position,
    inset CLR_BAY from the walls and pushed away from the bay's cutout."""
    if along_x:
        x_lo = x0 + P.CLR_BAY if near_min else x0 + w - P.CLR_BAY - length
        y_lo = y0 + P.CLR_BAY
        sx, sy = length, width
    else:
        x_lo = x0 + P.CLR_BAY
        y_lo = y0 + P.CLR_BAY if near_min else y0 + l - P.CLR_BAY - length
        sx, sy = width, length
    box = Pos(x_lo, y_lo, P.TRAY_PLATE) * Box(sx, sy, thickness, align=_MIN)
    return base.tray_seat() * box


def _roam_box():
    x0, y0, w, l = tray.ROAM_BAY
    return _device_box(x0, y0, w, l, m.ROAM.length, m.ROAM.width,
                        m.ROAM.thickness, along_x=False, near_min=False)


def _right_box(name, dev):
    x0, y0, w, l = tray.RIGHT_BAYS[name]
    return _device_box(x0, y0, w, l, dev.length, dev.width, dev.thickness,
                        along_x=True, near_min=True)


DEVICE_BOXES = {
    "roam": _roam_box,
    "trackr": lambda: _right_box("trackr", m.TRACKR),
    "ion": lambda: _right_box("ion", m.ION),
}


def _seated_divider(y):
    """The divider as exported -- the stack clearance only means anything
    against the part that actually gets printed."""
    x0, _, _, _ = tray.RIGHT_BAYS["ion"]
    placed = Pos(x0 + tray.RIGHT_BAY_W / 2, y, P.TRAY_PLATE) * PARTS["divider"]()
    return base.tray_seat() * placed


def _ceiling_z(seated_lid):
    """The underside of the seated lid's top plate: the highest downward
    horizontal face, measured on the solid."""
    return max(f.center().Z for f in seated_lid.faces().filter_by(Axis.Z)
               if f.normal_at().Z < 0)


# --- lid vs seated tray -------------------------------------------------------

def test_lid_seats_over_the_seated_tray_without_interference():
    """Here the design is contact, not clearance: the lid drops onto the
    base rim and the tray is flush with that rim, so the lid ceiling lands on
    the tray's top face.  Equal to within 1e-6 is what that looks like."""
    seated_lid, seated_tray = _seated_lid(), _seated_tray()
    assert (seated_lid & seated_tray).volume < 1e-3
    assert abs(_ceiling_z(seated_lid) - seated_tray.bounding_box().max.Z) < 1e-6


# --- devices on the seated tray vs the seated lid -----------------------------

def test_devices_on_the_seated_tray_clear_the_seated_lid():
    """Not merely out of the lid: every device finishes below its ceiling."""
    seated_lid = _seated_lid()
    ceiling = _ceiling_z(seated_lid)
    for name, box_fn in DEVICE_BOXES.items():
        box = box_fn()
        assert (box & seated_lid).volume < 1e-3, name
        gap = ceiling - box.bounding_box().max.Z
        assert gap > 0, f"{name} touches the lid ceiling"


# --- dividers on the seated tray vs base and lid ------------------------------

def test_dividers_on_the_seated_tray_clear_the_base_and_lid():
    p_base = base.build_base()
    seated_lid = _seated_lid()
    ceiling = _ceiling_z(seated_lid)
    for y in tray.RAIL_YS:
        seated_div = _seated_divider(y)
        assert (seated_div & p_base).volume < 1e-3, ("base", y)
        assert (seated_div & seated_lid).volume < 1e-3, ("lid", y)
        assert ceiling - seated_div.bounding_box().max.Z > 0, ("gap", y)


def test_the_seated_divider_stops_short_of_the_lid_ceiling():
    """The divider is the tallest loose part in the tray and it drops into
    its rails by hand, so it must not be what the lid lands on: measured on
    the seated solids, its top finishes clear of the lid ceiling."""
    ceiling = _ceiling_z(_seated_lid())
    for y in tray.RAIL_YS:
        gap = ceiling - _seated_divider(y).bounding_box().max.Z
        assert gap >= MIN_STACK_GAP, f"only {gap:.2f} mm of gap at y = {y:.1f}"


# --- assembled footprint -------------------------------------------------------

def test_assembled_footprint_fits_the_bed():
    s = _seated_lid().bounding_box().size
    assert s.X <= P.BED_X and s.Y <= P.BED_Y


# --- tray cable cutouts vs the base cavity ------------------------------------

def _tray_cutout_footprints():
    """Bounding boxes of the tray's cable cutouts, in base coordinates, read
    off the seated tray's underside: they are the only voids that go right
    through the plate, so they are its bottom face's inner wires."""
    bottom = _seated_tray().faces().filter_by(Axis.Z).sort_by(Axis.Z)[0]
    return [w.bounding_box() for w in bottom.inner_wires()]


def test_every_cable_cutout_drops_into_open_cavity():
    """A cable dropped through any cutout in the tray has to reach the cavity
    floor: it must not land on the charger, on the fence or on a cable loop.
    With the charger moved to the -X end wall the Roam bay's cutout is over
    the charger's X range, so this is measured, not assumed -- the column
    under every cutout, from the cavity floor up to the seated tray, is empty
    base.  (The Roam's cutout clears the charger in Y as well, so that cable
    drops straight past the charger's -Y side rather than over its top.)"""
    p_base = base.build_base()
    top = _seated_tray().bounding_box().min.Z      # the rebate ledge
    boxes = _tray_cutout_footprints()
    assert len(boxes) == 6, f"expected six cable cutouts, found {len(boxes)}"
    for bb in boxes:
        column = Pos(bb.center().X, bb.center().Y, P.FLOOR) * Box(
            bb.size.X - 0.02, bb.size.Y - 0.02, top - P.FLOOR,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        assert (column & p_base).volume < 1e-3, (
            f"a cutout at ({bb.center().X:.1f}, {bb.center().Y:.1f}) drops "
            f"onto solid base")
