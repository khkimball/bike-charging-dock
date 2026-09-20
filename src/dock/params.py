"""Design rules for the v2 tray dock. Millimetres. Change here, never inline
in a part module."""
from dataclasses import dataclass

from build123d import Align, Box, Part

WALL = 2.4         # 3 perimeters at 0.4 mm nozzle
FLOOR = 1.6        # 4 layers at 0.4 mm
CHAMFER = 1.0      # downward-facing edge chamfer
CLR_FIT = 0.15     # coupon 2026-09-20, PLA on U1: 0.10 tight, 0.15 slides
CLR_RAIL = 0.20    # one step above CLR_FIT so the divider drops in by hand
CLR_BAY = 3.0      # device to bay wall, per side (bays, not pockets)
TRAY_PLATE = 3.0   # tray floor thickness (cable cutouts pass through it)
BAY_DEPTH = 28.0   # bay wall height above the tray plate
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


# Typical overmold sizes; refine from the actual cables when measured.
USB_A_PLUG = Plug(width=15.0, height=8.0, length=20.0)
USB_C_PLUG = Plug(width=11.0, height=6.0, length=18.0)
MICRO_PLUG = Plug(width=10.5, height=6.5, length=17.0)
# The bare cable behind the USB-C overmold, not the overmold itself: this is
# what the Roam cradle's cable slot has to pass.
USB_C_CABLE = Plug(width=6.0, height=4.0, length=30.0)


_CTR = (Align.CENTER, Align.CENTER, Align.CENTER)


def plug_cutter(plug: Plug, length: float = THRU) -> Part:
    """Cutter for a plug overmold: the envelope plus CLR_BAY per side.

    Centred on the origin, `length` long in Z, so callers place and rotate
    it.  Pass `THRU` (the default) for a cut that runs clear of the part.
    """
    return Box(plug.width + 2 * CLR_BAY,
               plug.height + 2 * CLR_BAY,
               length, align=_CTR)
