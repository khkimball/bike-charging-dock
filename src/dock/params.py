"""Design rules for the tapered dock. Millimetres. Change here, never inline
in a part module."""
from dataclasses import dataclass

WALL = 2.0         # base shell and tray dividers: 5 lines at 0.4 mm (v1: 2.4)
THIN_WALL = 1.6    # 2 perimeters a side: the tray's hidden outer walls, the lid's walls
FLOOR = 1.2        # base floor: 6 layers at 0.2 mm (v1: 1.6)
CHAMFER = 1.0      # downward-facing edge chamfer
CLR_FIT = 0.15     # coupon 2026-09-20, PLA on U1: 0.10 tight, 0.15 slides
CLR_BAY = 8.0      # device to a vertical (internal) bay wall; room for the cable beside it
CLR_BAY_OUTER = 3.0  # device to a sloped (outer) bay wall at the floor; the lean opens it
                     # to ~13 mm by the rim
TRAY_PLATE = 1.2   # tray floor: 6 layers; cable cutouts pass through it (v1: 3.0)
LID_PLATE = 1.2    # lid top: 6 layers
BAY_DEPTH = 38.0   # bay wall height above the tray plate (v2.1: was 32); must clear the
                   # tallest device (ION 30.2) so the lid does not touch it
TAPER_DEG = 15.0   # every outer face leans this far off vertical, like the Trek CHRGtime
CORNER_R = 30.0    # base rim corner radius; the draft shrinks it to ~R8 at the foot
BAND_H = 8.0       # colour line: dark foot band below, light body above
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
