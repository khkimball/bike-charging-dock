"""Export every registered part into out/, then report the numbers worth
checking before a print: what each part measures, and how much room is left
around the charger inside the base."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import base
from dock import coupon
from dock import divider
from dock import hinge
from dock import layout
from dock import lid
from dock import params
from dock import tray


def _coupon_plate() -> Part:
    return coupon.build_coupon()[0]


def _coupon_peg() -> Part:
    return coupon.build_coupon()[1]


def _hinge_coupon_base() -> Part:
    return coupon.build_hinge_coupon()[0]


def _hinge_coupon_lid() -> Part:
    return coupon.build_hinge_coupon()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "coupon_plate": _coupon_plate,
    "coupon_peg": _coupon_peg,
    "hinge_coupon_base": _hinge_coupon_base,
    "hinge_coupon_lid": _hinge_coupon_lid,
}

PARTS.update({
    "base": base.build_base,
    "tray": tray.build_tray,
    "lid": lid.build_lid,
    # Sized from the tray's right column: the slab is narrower than the bay by
    # CLR_RAIL, and each rail adds RAIL_D beyond it into the wall slots.  It
    # is half a millimetre shorter than the bay is deep, so the lid lands on
    # the tray rim and never on a divider that has not quite seated.
    "divider": lambda: divider.build_divider(
        height=params.BAY_DEPTH - 0.5,
        width=tray.RIGHT_BAY_W - params.CLR_RAIL),
})


def build_report() -> str:
    """The derived sizes and clearances, in mm, read off the built parts.
    Every one of them moves on its own when a measurement or a design rule
    changes, so print them where they can be read before a long print."""
    lines = ["build report (mm, as printed)"]
    for name in ("base", "tray", "lid"):
        s = PARTS[name]().bounding_box().size
        lines.append(f"  {name:<5}{s.X:8.2f} x {s.Y:7.2f} x {s.Z:6.2f}")
    lines += [
        f"  charger fence: {base.FENCE_MARGIN_Y:.2f} free each side; port room "
        f"{base.PORT_PLUG_ROOM:.2f} (need {base.PORT_PLUG_ROOM_MIN:.2f})",
        f"  lid lip {layout.LIP_W:.2f} proud; hinge opens to {hinge.OPEN_DEG:.0f} deg",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
    print()
    print(build_report())
