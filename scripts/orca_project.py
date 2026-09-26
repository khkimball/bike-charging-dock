"""Build one Snapmaker Orca project with every printed part on its own plate:
Base, Tray, Lid, Hinge test (both halves), Fit test (plate + peg).

    uv run python scripts/export_all.py        # first: fresh out/*.stl
    uv run python scripts/orca_project.py      # -> out/orca/dock_plates.3mf
    flatpak run --filesystem=$PWD io.github.Snapmaker.Snapmaker_Orca $PWD/out/orca/dock_plates.3mf

Orca's CLI can't be asked for plates directly in this Flatpak build: its
`--load-assemble-list` segfaults, and it segfaults loading any 3mf.  What
does work is `--arrange` over plain STLs, which lays them onto as many
plates as it needs, in whatever grouping it likes.  So this arranges them
once for a valid project file, then rewrites the plate assignment and
each object's position to the grouping above.  Plates sit on Orca's grid:
PLATE_STRIDE apart (1.2 x the 270 mm U1 bed), COLS to a row, each object
centred on its plate.  The printer, process and filament are the U1 / 0.20
Standard / Generic PETG profiles slice_report.py flattens (run it once).
"""
import math
import re
import subprocess
import sys
import zipfile
from pathlib import Path

APP = "io.github.Snapmaker.Snapmaker_Orca"
OUT = Path("out/orca")
PROFILES = Path("out/slice")
PLATES = [  # (plate name, [(part, dx, dy) offset from the plate centre])
    ("Base", [("base", 0, 0)]),
    ("Tray", [("tray", 0, 0)]),
    ("Lid", [("lid", 0, 0)]),
    ("Hinge test", [("hinge_test_base", -34, 0), ("hinge_test_lid", 34, 0)]),
    ("Fit test", [("fit_test_plate", 0, -12), ("fit_test_peg", 0, 18)]),
]
BED_CENTRE = (135.5, 136.0)      # U1 printable area 0.5..270.5 x 1..271
PLATE_STRIDE = 324.0             # Orca spaces plates 1.2 bed-widths apart


def _cols(n: int) -> int:
    """Orca's plate-grid column count for n plates."""
    v = math.sqrt(n)
    return int(round(v)) + (1 if v > round(v) else 0)


def _arranged(stls: list[Path], dst: Path) -> None:
    prof = PROFILES.resolve()
    for f in ("machine.json", "process_0.20.json", "filament.json"):
        if not (prof / f).exists():
            sys.exit(f"missing {prof / f} -- run scripts/slice_report.py once first")
    cmd = ["flatpak", "run", f"--filesystem={Path.cwd()}", APP,
           "--load-settings", f"{prof / 'machine.json'};{prof / 'process_0.20.json'}",
           "--load-filaments", str(prof / "filament.json"),
           "--arrange", "1", "--export-3mf", dst.name, "--outputdir", str(dst.parent.resolve()),
           *[str(s.resolve()) for s in stls]]
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode != 0 or not dst.exists():
        sys.exit(f"orca --arrange failed (exit {run.returncode}):\n{run.stderr[-2000:]}")


def _replan(src: Path, dst: Path) -> None:
    with zipfile.ZipFile(src) as z:
        files = {i.filename: z.read(i.filename) for i in z.infolist()}
    model = files["3D/3dmodel.model"].decode()
    ms = files["Metadata/model_settings.config"].decode()

    names = {n.removesuffix(".stl"): oid for oid, n in re.findall(
        r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', ms)}
    offset = {}   # the component offset from each object's origin to its mesh centre
    for oid, body in re.findall(r'<object id="(\d+)"[^>]*>(.*?)</object>', model, re.S):
        m = re.search(r'<component [^>]*transform="([^"]+)"', body)
        if m:
            t = [float(v) for v in m.group(1).split()]
            offset[oid] = (t[9], t[10])
    ident = dict(re.findall(r'<metadata key="object_id" value="(\d+)"/>\s*'
                            r'<metadata key="instance_id" value="0"/>\s*'
                            r'<metadata key="identify_id" value="(\d+)"/>', ms))

    cols = _cols(len(PLATES))
    pos = {}
    for i, (_, objs) in enumerate(PLATES):
        ox, oy = (i % cols) * PLATE_STRIDE, -(i // cols) * PLATE_STRIDE
        for part, dx, dy in objs:
            oid = names[part]
            cx, cy = offset[oid]
            pos[oid] = (ox + BED_CENTRE[0] + dx - cx, oy + BED_CENTRE[1] + dy - cy)

    def item(m):
        x, y = pos[m.group(1)]
        return re.sub(r'transform="[^"]+"', f'transform="1 0 0 0 1 0 0 0 1 {x:.4f} {y:.4f} 0"',
                      m.group(0))
    model = re.sub(r'<item objectid="(\d+)"[^>]*/>', item, model)

    plates = []
    for i, (name, objs) in enumerate(PLATES, 1):
        inst = "".join(
            "    <model_instance>\n"
            f'      <metadata key="object_id" value="{names[p]}"/>\n'
            '      <metadata key="instance_id" value="0"/>\n'
            f'      <metadata key="identify_id" value="{ident[names[p]]}"/>\n'
            "    </model_instance>\n" for p, _, _ in objs)
        plates.append(
            "  <plate>\n"
            f'    <metadata key="plater_id" value="{i}"/>\n'
            f'    <metadata key="plater_name" value="{name}"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            '    <metadata key="filament_maps" value="1"/>\n'
            '    <metadata key="gcode_file" value=""/>\n'
            f"{inst}  </plate>\n")
    ms = ms[:ms.index("  <plate>")] + "".join(plates) + ms[ms.index("  <assemble>"):]

    files["3D/3dmodel.model"] = model.encode()
    files["Metadata/model_settings.config"] = ms.encode()
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def main() -> int:
    stls = [Path("out") / f"{p}.stl" for _, objs in PLATES for p, _, _ in objs]
    missing = [s for s in stls if not s.exists()]
    if missing:
        sys.exit(f"missing {', '.join(map(str, missing))} -- run scripts/export_all.py")
    OUT.mkdir(parents=True, exist_ok=True)
    arranged = OUT / "arranged.3mf"
    _arranged(stls, arranged)
    dst = OUT / "dock_plates.3mf"
    _replan(arranged, dst)
    arranged.unlink()
    print(dst.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
