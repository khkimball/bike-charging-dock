"""The draft every outer face of the dock shares, and the rounded outlines
it is built from.

The Trek CHRGtime's walls lean about 15 degrees off vertical (measured off
its manual's to-scale front view), and so do this dock's -- base, lid and
the tray inside, one continuous slope from the lid top to the foot.  It is a
true draft: an Outline carried down by d mm steps in d*TAN on every side and
its corner radius shrinks by the same, so everything derived from one
Outline stays concentric with it, corners included.  That is what keeps a
wall a constant thickness through its corners, and the gap between the tray
and the base uniform all the way round.
"""
import math
from dataclasses import dataclass

from build123d import Part, Plane, Pos, Rectangle, RectangleRounded, Sketch, Vector, fillet, loft

from dock import params as P

TAN = math.tan(math.radians(P.TAPER_DEG))
COS = math.cos(math.radians(P.TAPER_DEG))


def horiz(t: float) -> float:
    """Horizontal width of a wall `t` thick measured square to a drafted face."""
    return t / COS


def bed_chamfer_inset() -> float:
    """Extra inset at the bed that makes a drafted wall's foot chamfer 45
    degrees: the draft already steps the outline in CHAMFER*TAN over it."""
    return P.CHAMFER * (1 - TAN)


@dataclass(frozen=True)
class Outline:
    """A rounded rectangle centred on the Z axis: `sx` by `sy`, corner radius
    `r`, at height `z_ref`.  Carried up or down the draft it grows or shrinks
    by TAN per mm on every side, radius included."""
    sx: float
    sy: float
    r: float
    z_ref: float

    def at(self, z: float, inset: float = 0.0) -> tuple[float, float, float]:
        """(sx, sy, r) at height z, then moved `inset` further in (negative: out)."""
        i = inset + (self.z_ref - z) * TAN
        return self.sx - 2 * i, self.sy - 2 * i, self.r - i

    def section(self, z: float, inset: float = 0.0) -> Sketch:
        sx, sy, r = self.at(z, inset)
        if r <= 0:
            raise ValueError(f"corner radius {r:.2f} at z={z:.2f}: the draft ran it out")
        return Plane.XY.offset(z) * RectangleRounded(sx, sy, r)

    def solid(self, z0: float, z1: float, inset: float = 0.0) -> Part:
        """The drafted solid between z0 and z1, `inset` in from this outline."""
        return loft([self.section(z0, inset), self.section(z1, inset)])


_CORNERS = {"--": (0, 2), "+-": (1, 2), "++": (1, 3), "-+": (0, 3)}


def corner_rect(x0: float, x1: float, y0: float, y1: float,
                radii: dict[str, float], z: float) -> Sketch:
    """Rectangle x0..x1 by y0..y1 at height z, each corner rounded by its own
    radius.  Keys "--", "+-", "++", "-+" name a corner by the signs of its X
    and Y; a missing key or a radius of 0 leaves that corner square."""
    s = Pos((x0 + x1) / 2, (y0 + y1) / 2) * Rectangle(x1 - x0, y1 - y0)
    xy = (x0, x1, y0, y1)
    for key, r in radii.items():
        if r <= 0:
            continue
        ix, iy = _CORNERS[key]
        s = fillet(s.vertices().sort_by_distance(Vector(xy[ix], xy[iy], 0))[0], r)
    return Plane.XY.offset(z) * s
