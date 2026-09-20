"""Export every registered part into out/."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import coupon
from dock import divider
from dock import params
from dock import tray


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
}

PARTS.update({
    "tray": tray.build_tray,
    # Sized from the tray's right column: the slab is narrower than the bay by
    # CLR_RAIL, and each rail adds RAIL_D beyond it into the wall slots.
    "divider": lambda: divider.build_divider(
        height=params.BAY_DEPTH, width=tray.RIGHT_BAY_W - params.CLR_RAIL),
})

if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
