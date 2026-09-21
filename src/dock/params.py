"""Design rules for the v2 tray dock. Millimetres. Change here, never inline
in a part module."""
from dataclasses import dataclass

WALL = 2.4         # 3 perimeters at 0.4 mm nozzle
FLOOR = 1.6        # 4 layers at 0.4 mm
CHAMFER = 1.0      # downward-facing edge chamfer
CLR_FIT = 0.15     # coupon 2026-09-20, PLA on U1: 0.10 tight, 0.15 slides
CLR_RAIL = 0.20    # one step above CLR_FIT so the divider drops in by hand
CLR_BAY = 8.0      # device to bay wall, per side; room for the cable beside the device (v2.1: was 3.0, too tight with cables)
TRAY_PLATE = 3.0   # tray floor thickness (cable cutouts pass through it)
BAY_DEPTH = 38.0   # bay wall height above the tray plate (v2.1: was 32); must clear the
                   # tallest device (ION 30.2) so the lid does not touch it
CORNER_R = 8.0     # fillet on the base/lid outer vertical edges
BED_X = 250        # U1 usable X with margin
BED_Y = 250        # U1 usable Y with margin
THRU = 400.0       # cutter length; longer than any part in this design


@dataclass(frozen=True)
class Plug:
    """Cable connector overmold envelope (the moulded body, not the metal tip)."""
    width: float
    height: float
    length: float   # overmold length along the cable axis


# Typical overmold sizes; refine from the actual cables when measured.  The
# tray's cable cutouts are one size for all of them (see tray.CUTOUT), so
# these are sanity limits, not cutter inputs.
USB_A_PLUG = Plug(width=15.0, height=8.0, length=20.0)
USB_C_PLUG = Plug(width=11.0, height=6.0, length=18.0)
MICRO_PLUG = Plug(width=10.5, height=6.5, length=17.0)
