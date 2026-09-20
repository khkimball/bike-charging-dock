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
from build123d import Align, Box, Pos

from dock import base, divider, lid, tray
from dock import measurements as m
from dock import params as P

_MIN = (Align.MIN, Align.MIN, Align.MIN)


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
    x0, _, w, _ = tray.RIGHT_BAYS["ion"]
    d = divider.build_divider(height=P.BAY_DEPTH, width=tray.RIGHT_BAY_W - P.CLR_RAIL)
    placed = Pos(x0 + tray.RIGHT_BAY_W / 2, y, P.TRAY_PLATE) * d
    return base.tray_seat() * placed


# --- lid vs seated tray -------------------------------------------------------

def test_lid_seats_over_the_seated_tray_without_interference():
    assert (_seated_lid() & _seated_tray()).volume < 1e-3


# --- devices on the seated tray vs the seated lid -----------------------------

def test_bay_depth_clears_the_tallest_device():
    """Precondition for the clearance check below: the walls (and so the
    seated lid, which rests on them) stand at or above every device."""
    tallest = max(d.thickness for d in (m.ROAM, m.ION, m.TRACKR))
    assert P.BAY_DEPTH >= tallest


def test_devices_on_the_seated_tray_clear_the_seated_lid():
    seated_lid = _seated_lid()
    for name, box_fn in DEVICE_BOXES.items():
        assert (box_fn() & seated_lid).volume < 1e-3, name


# --- dividers on the seated tray vs base and lid ------------------------------

def test_dividers_on_the_seated_tray_clear_the_base_and_lid():
    p_base = base.build_base()
    seated_lid = _seated_lid()
    for y in tray.RAIL_YS:
        seated_div = _seated_divider(y)
        assert (seated_div & p_base).volume < 1e-3, ("base", y)
        assert (seated_div & seated_lid).volume < 1e-3, ("lid", y)


# --- assembled footprint -------------------------------------------------------

def test_assembled_footprint_fits_the_bed():
    s = _seated_lid().bounding_box().size
    assert s.X <= P.BED_X and s.Y <= P.BED_Y
