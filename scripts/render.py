"""Render the assembled dock to docs/images/*.png for the README and listings.

    uv run python scripts/render.py

A small z-buffer rasteriser over build123d's tessellation (numpy + Pillow,
both already installed with build123d), so the renders need no viewer or
extra dependency.  Orthographic, two-sided Lambert shading, 2x supersampled.
The base's band below params.BAND_H is drawn in the dark filament.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from dock import base, lid, params as P, tray
from dock import hinge as H

OUT = Path("docs/images")
SIZE = 1200                    # output width and height, px
SS = 2                         # supersampling
DARK = np.array([0.17, 0.18, 0.20])
LIGHT = np.array([0.91, 0.90, 0.87])
LIGHT_DIR = np.array([-0.35, -0.55, 0.76])


def _mesh(part, colour_of_z=None):
    """(triangles Nx3x3, colours Nx3) of a part."""
    verts, tris = part.tessellate(0.02, 0.06)
    v = np.array([[p.X, p.Y, p.Z] for p in verts])
    t = v[np.array(tris)]
    if colour_of_z is None:
        c = np.tile(LIGHT, (len(t), 1))
    else:
        c = np.array([colour_of_z(z) for z in t[:, :, 2].mean(axis=1)])
    return t, c


def _two_tone(z):
    return DARK if z < P.BAND_H else LIGHT


def _view(az: float, el: float) -> np.ndarray:
    """Rotation taking world to camera (x right, y up, z towards the viewer)
    for a camera at azimuth `az` (degrees from -Y, towards +X) and elevation `el`."""
    a, e = np.radians(az), np.radians(el)
    eye = np.array([np.sin(a) * np.cos(e), -np.cos(a) * np.cos(e), np.sin(e)])
    up = np.array([0.0, 0.0, 1.0]) if abs(el) < 89 else np.array([0.0, 1.0, 0.0])
    right = np.cross(up, eye)
    right /= np.linalg.norm(right)
    return np.array([right, np.cross(eye, right), eye])


def render(meshes, az, el, path: Path) -> None:
    tris = np.concatenate([m[0] for m in meshes])
    cols = np.concatenate([m[1] for m in meshes])
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = LIGHT_DIR / np.linalg.norm(LIGHT_DIR)
    shade = 0.35 + 0.65 * np.abs(n @ light)
    cols = np.clip(cols * shade[:, None], 0, 1)

    cam = tris @ _view(az, el).T
    lo, hi = cam[:, :, :2].reshape(-1, 2).min(0), cam[:, :, :2].reshape(-1, 2).max(0)
    w = SIZE * SS
    scale = 0.9 * w / (hi - lo).max()
    xy = (cam[:, :, :2] - (lo + hi) / 2) * scale + w / 2
    xy[:, :, 1] = w - xy[:, :, 1]
    z = cam[:, :, 2]

    img = np.ones((w, w, 4))
    img[:, :, 3] = 0.0
    zbuf = np.full((w, w), -np.inf)
    for (p0, p1, p2), (z0, z1, z2), c in zip(xy, z, cols):
        x0, y0 = np.floor(np.minimum(np.minimum(p0, p1), p2)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(p0, p1), p2)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, w - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-9:
            continue
        l0 = ((p1[1] - p2[1]) * (gx - p2[0]) + (p2[0] - p1[0]) * (gy - p2[1])) / d
        l1 = ((p2[1] - p0[1]) * (gx - p2[0]) + (p0[0] - p2[0]) * (gy - p2[1])) / d
        l2 = 1 - l0 - l1
        inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        depth = l0 * z0 + l1 * z1 + l2 * z2
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        hit = inside & (depth > sub)
        sub[hit] = depth[hit]
        img[y0:y1 + 1, x0:x1 + 1][hit] = (*c, 1.0)

    out = Image.fromarray((img * 255).astype(np.uint8), "RGBA").resize((SIZE, SIZE), Image.LANCZOS)
    out.crop(out.getbbox()).save(path, optimize=True)
    print(path)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    b = _mesh(base.build_base(), _two_tone)
    t = _mesh(base.tray_seat() * tray.build_tray())
    printed_lid = lid.build_lid()
    closed = _mesh(lid.lid_seat(0) * printed_lid)
    opened = _mesh(lid.lid_seat(H.OPEN_DEG - 1) * printed_lid)
    render([b, t, closed], 35, 25, OUT / "dock_closed.png")
    render([b, t, opened], 35, 30, OUT / "dock_open.png")
    render([b, t], 0, 90, OUT / "tray_top.png")
    render([b], 210, 30, OUT / "base_back.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
