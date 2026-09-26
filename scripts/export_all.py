"""Export every registered part into out/, then report the numbers worth
checking before a print: what each part measures, and how much room is left
around the charger inside the base."""
from typing import Callable
from build123d import Part
from dock.export import write_all
from dock import base
from dock import fit_tests
from dock import hinge
from dock import layout
from dock import lid
from dock import tray


def _fit_test_plate() -> Part:
    return fit_tests.build_fit_test()[0]


def _fit_test_peg() -> Part:
    return fit_tests.build_fit_test()[1]


def _hinge_test_base() -> Part:
    return fit_tests.build_hinge_test()[0]


def _hinge_test_lid() -> Part:
    return fit_tests.build_hinge_test()[1]


PARTS: dict[str, Callable[[], Part]] = {
    "fit_test_plate": _fit_test_plate,
    "fit_test_peg": _fit_test_peg,
    "hinge_test_base": _hinge_test_base,
    "hinge_test_lid": _hinge_test_lid,
    "base": base.build_base,
    "tray": tray.build_tray,
    "lid": lid.build_lid,
}


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
