"""Export every registered part into out/."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import coupon


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
}

if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
