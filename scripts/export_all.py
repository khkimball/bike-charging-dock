"""Export every registered part into out/."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import base
from dock import coupon
from dock import cradles
from dock import deck
from dock import divider


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
}

PARTS.update({
    "cradle_roam": cradles.build_roam_cradle,
    "cradle_ion": cradles.build_ion_cradle,
    "cradle_trackr": cradles.build_trackr_cradle,
})

PARTS.update({
    "divider": lambda: divider.build_divider(40, 50),
})

PARTS.update({
    "deck": deck.build_deck,
})

PARTS.update({
    "base": base.build_base,
})

if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
