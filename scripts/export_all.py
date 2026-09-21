"""Export every registered part into out/, then report the numbers worth
checking before a print: what each part measures, and how much room is left
around the charger inside the base."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import base
from dock import coupon
from dock import divider
from dock import lid
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
    """The derived sizes and clearances, in mm.  Every one of them moves on
    its own when a measurement or a design rule changes, so print them where
    they can be read before committing to a six-hour print."""
    return "\n".join((
        "build report (mm)",
        f"  base   {base.BASE_X:7.2f} x {base.BASE_Y:7.2f} x {base.BASE_H:6.2f}",
        f"  tray   {tray.TRAY_X:7.2f} x {tray.TRAY_Y:7.2f} x {tray.TRAY_H:6.2f}",
        f"  lid    {lid.LID_X:7.2f} x {lid.LID_Y:7.2f} x {lid.LID_H:6.2f}",
        f"  cavity room past the fence: X {base.FENCE_MARGIN_X:.2f} in "
        f"front, Y {base.FENCE_MARGIN_Y:.2f} per side",
        f"  charger backed against the -X wall; port room "
        f"{base.PORT_PLUG_ROOM:.2f} (need {base.PORT_PLUG_ROOM_MIN:.2f})",
    ))


if __name__ == "__main__":
    for name, fn in PARTS.items():
        for p in write_all(fn(), name):
            print(p)
    print()
    print(build_report())
