"""Design rules. Millimetres. Change here, never inline in a part module."""
from dataclasses import dataclass

WALL = 2.4        # 3 perimeters at 0.4 mm nozzle
FLOOR = 1.6       # 4 layers at 0.4 mm
CHAMFER = 1.0     # downward-facing edge chamfer
CLR_DEVICE = 0.3  # device pocket clearance per side
CLR_FIT = 0.2     # deck lip into base
CLR_RAIL = 0.25   # divider dovetail rails
BED_X = 250       # U1 usable X with margin
BED_Y = 120       # self-imposed footprint limit
THRU = 400.0      # cutter length; longer than any part in this design


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
