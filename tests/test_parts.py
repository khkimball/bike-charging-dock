"""Checks that every exported part is printable as exported."""
import sys
from pathlib import Path

import pytest
from build123d import Axis

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_all import PARTS  # noqa: E402  (needs the path insert above)


@pytest.mark.parametrize("name", sorted(PARTS))
def test_exported_part_is_one_valid_solid_on_the_bed(name):
    part = PARTS[name]()
    assert part.is_valid, f"{name} is not a valid solid"
    assert len(part.solids()) == 1, f"{name} exports {len(part.solids())} solids"
    bottom = part.faces().sort_by(Axis.Z)[0]
    assert abs(bottom.center().Z) < 1e-6, f"{name} does not sit on Z=0"
