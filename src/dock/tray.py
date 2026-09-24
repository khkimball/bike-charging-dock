"""Tray: four bays for devices lying face up, in a tapered shell that
nests in the base.

The bays are laid out in layout.py -- ROAM on the left, spare/TRACKR/Ion
stacked on the right -- and each is cut as its own void: a loft from the bay
floor up past the rim, leaning out at the draft on the sides that lie on the
tray's outer wall and standing vertical on the internal ones.  The material
left between the voids is the partition and the two dividers, fixed and
printed with the tray.  Each void's corners are rounded before it is cut:
INNER_FILLET_R where it meets an internal wall, the tray's own corner radius
(less the wall) where it meets two outer walls, so the shell keeps its
thickness through those corners.  Its floor edges are rounded
FLOOR_FILLET_R, and once all four are cut the tops of the walls are rounded
TOP_ROUND_R.  All of these face up or sideways, so they print.

The tray is lifted out by the partition, through a finger slot with a 45
degree pointed head.  Cable cutouts are ovals through the plate, where
layout.py puts them.

Tray coordinates: XY centred, plate underside at Z = 0.  Printed plate-down,
bays up; nothing overhangs.
"""
from build123d import Axis, Part, Plane, Polygon, Pos, SlotCenterToCenter, extrude, fillet, loft

from dock import layout as L
from dock import params as P
from dock import taper

WALL_H = taper.horiz(P.THIN_WALL)      # the outer wall, measured horizontally
TRAY_H = L.TRAY_H
TRAY_X, TRAY_Y = L.TRAY_OUTLINE.sx, L.TRAY_OUTLINE.sy     # at the rim
TOP_ROUND_R = 0.8     # a full round of a WALL-thick top would leave no face to fillet
SLOT_W = 25.0
SLOT_H = 15.0
SLOT_TOP_DROP = 5.0   # slot apex below the rim
PARTITION_X = L.BAYS["roam"].x1 + P.WALL / 2
_OVER = 5.0           # voids run this far past the rim
_CORNER_SIDES = {"--": (0, 2), "+-": (1, 2), "++": (1, 3), "-+": (0, 3)}


def _void_radii(b: L.Bay, z: float) -> dict[str, float]:
    outer_r = L.TRAY_OUTLINE.at(z, WALL_H)[2]
    return {k: outer_r if (b.sloped[i] and b.sloped[j]) else L.INNER_FILLET_R
            for k, (i, j) in _CORNER_SIDES.items()}


def _bay_void(b: L.Bay) -> Part:
    z0, z1 = P.TRAY_PLATE, TRAY_H + _OVER
    g = [(z1 - z0) * taper.TAN if s else 0.0 for s in b.sloped]
    lo = taper.corner_rect(b.x0, b.x1, b.y0, b.y1, _void_radii(b, z0), z0)
    hi = taper.corner_rect(b.x0 - g[0], b.x1 + g[1], b.y0 - g[2], b.y1 + g[3],
                           _void_radii(b, z1), z1)
    void = loft([lo, hi])
    return fillet(void.faces().sort_by(Axis.Z)[0].edges(), L.FLOOR_FILLET_R)


def _finger_slot() -> Part:
    top = TRAY_H - SLOT_TOP_DROP
    bot = top - SLOT_H
    shoulder = top - SLOT_W / 2          # 45-degree head
    pts = [(-SLOT_W / 2, bot), (SLOT_W / 2, bot), (SLOT_W / 2, shoulder),
           (0.0, top), (-SLOT_W / 2, shoulder)]
    face = Plane.YZ.offset(PARTITION_X - P.WALL) * Polygon(*pts, align=None)
    return extrude(face, amount=2 * P.WALL)


def build_tray() -> Part:
    part = L.TRAY_OUTLINE.solid(P.CHAMFER, TRAY_H) + loft(
        [L.TRAY_OUTLINE.section(0.0, taper.bed_chamfer_inset()),
         L.TRAY_OUTLINE.section(P.CHAMFER)])
    for b in L.BAYS.values():
        part -= _bay_void(b)
    top = part.faces().sort_by(Axis.Z)[-1]
    part = fillet([e for w in top.inner_wires() for e in w.edges()], TOP_ROUND_R)
    part -= _finger_slot()
    for _, cx, cy, sx, sy in L.cutouts():
        long, short = max(sx, sy), min(sx, sy)
        oval = SlotCenterToCenter(long - short, short, rotation=0 if sx >= sy else 90)
        part -= Pos(cx, cy, -1.0) * extrude(oval, amount=P.TRAY_PLATE + 2.0)
    return part
