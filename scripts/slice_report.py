"""Slice the exported parts headlessly in Snapmaker Orca and report print
time and filament for each, next to the v1 baseline.

    uv run python scripts/slice_report.py                  # 0.20 Standard, the dock set in out/
    uv run python scripts/slice_report.py --layer 0.28     # 0.28 Extra Draft
    uv run python scripts/slice_report.py releases/v1-prototype/tray.stl

It needs the Snapmaker Orca Flatpak and takes minutes, so it is not part of
pytest.  The profiles are the vendor's own -- Snapmaker U1 (0.4 nozzle), the
0.20 Standard or 0.28 Extra Draft process, Generic PETG -- flattened at run
time, with the per-part settings from docs/printing.md laid over them: three
walls and 15 % infill everywhere, supports only for the lid (its hook bores).

The Orca CLI in this Flatpak has three quirks, each handled below:
- system profiles `inherits` from one another and the CLI will not follow
  the chain, so each is flattened into one standalone JSON first -- keeping
  `"from": "system"`, because a flattened "User" process is then reported as
  incompatible with the printer (return code -17);
- any process carrying the key `wipe_tower_filament` segfaults it (exit 139),
  so that key is dropped;
- `--export-3mf` is joined onto `--outputdir`, so it gets a bare file name.
The estimates are read from the gcode header inside the exported 3mf.
"""
import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

APP = "io.github.Snapmaker.Snapmaker_Orca"
MACHINE = "Snapmaker U1 (0.4 nozzle)"
PROCESS = {"0.20": "0.20 Standard @Snapmaker U1 (0.4 nozzle)",
           "0.28": "0.28 Extra Draft @Snapmaker U1 (0.4 nozzle)"}
FILAMENT = "Generic PETG"
SUPPORTED = {"lid"}              # parts that print with supports
DOCK_SET = ("base", "tray", "lid")
# The v1 prototype's STLs (releases/v1-prototype/) through this same script
# at 0.20, 2026-09-24: (minutes, grams) per part, and how many of each part a
# v1 set needed.  Re-run it on those STLs if the Flatpak's profiles change.
BASELINE = {"base": (355, 263.7), "tray": (262, 184.5), "lid": (135, 103.8),
            "divider": (44, 15.2)}
BASELINE_COUNT = {"base": 1, "tray": 1, "lid": 1, "divider": 2}
OUT = Path("out/slice")


def _profiles_root() -> Path:
    loc = subprocess.run(["flatpak", "info", "--show-location", APP],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(loc) / "files/share/Snapmaker_Orca/profiles"


def _index(root: Path, kind: str) -> dict[str, Path]:
    """name -> file for every `kind` (machine/process/filament) profile."""
    idx: dict[str, Path] = {}
    for fp in root.rglob(f"{kind}/*.json"):
        try:
            name = json.loads(fp.read_text()).get("name")
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if name and name not in idx:
            idx[name] = fp
    return idx


def _flatten(idx: dict[str, Path], name: str) -> dict:
    d = json.loads(idx[name].read_text())
    parent = d.pop("inherits", None)
    merged = _flatten(idx, parent) if parent else {}
    merged.update(d)
    merged["from"] = "system"
    merged.pop("inherits", None)
    return merged


def _write(d: dict, path: Path) -> Path:
    path.write_text(json.dumps(d, indent=4))
    return path.resolve()


def _minutes(text: str) -> float:
    total = 0.0
    for n, unit in re.findall(r"(\d+)([dhms])", text):
        total += int(n) * {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}[unit]
    return total


def _estimates(threemf: Path) -> tuple[float, float]:
    with zipfile.ZipFile(threemf) as z:
        gcode = next(n for n in z.namelist() if n.endswith(".gcode"))
        head = z.read(gcode).decode(errors="replace")
    t = re.search(r"estimated printing time \(normal mode\) = ([^\n]+)", head)
    g = re.search(r"total filament used \[g\] = ([\d.]+)", head)
    if not (t and g):
        raise RuntimeError(f"no estimates in {threemf}")
    return _minutes(t.group(1)), float(g.group(1))


def slice_part(stl: Path, layer: str, prof: dict[str, Path]) -> tuple[float, float]:
    name = stl.stem
    outdir = (OUT / f"{name}_{layer}").resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    process = prof["support" if name in SUPPORTED else "plain"]
    cmd = ["flatpak", "run", f"--filesystem={OUT.resolve()}",
           f"--filesystem={stl.resolve().parent}", APP,
           "--load-settings", f"{prof['machine']};{process}",
           "--load-filaments", str(prof["filament"]),
           "--slice", "0", "--export-3mf", f"{name}.3mf",
           "--outputdir", str(outdir), str(stl.resolve())]
    run = subprocess.run(cmd, capture_output=True, text=True)
    result = outdir / "result.json"
    rc = json.loads(result.read_text()).get("return_code") if result.exists() else None
    if run.returncode != 0 or rc not in (0, None):
        raise RuntimeError(f"{name}: orca exit {run.returncode}, return_code {rc}\n"
                           f"{run.stderr[-2000:]}")
    return _estimates(outdir / f"{name}.3mf")


def _fmt(minutes: float) -> str:
    total = round(minutes)          # round first, so h/m split never carries a 60
    return f"{total // 60}h{total % 60:02d}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stls", nargs="*", type=Path)
    ap.add_argument("--layer", choices=sorted(PROCESS), default="0.20")
    args = ap.parse_args()
    stls = args.stls or [Path("out") / f"{n}.stl" for n in DOCK_SET]
    missing = [s for s in stls if not s.exists()]
    if missing:
        print(f"missing: {', '.join(map(str, missing))} -- run scripts/export_all.py",
              file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    root = _profiles_root()
    proc = _flatten(_index(root, "process"), PROCESS[args.layer])
    proc.pop("wipe_tower_filament", None)
    proc.update({"wall_loops": "3", "sparse_infill_density": "15%"})
    prof = {
        "machine": _write(_flatten(_index(root, "machine"), MACHINE), OUT / "machine.json"),
        "filament": _write(_flatten(_index(root, "filament"), FILAMENT), OUT / "filament.json"),
        "plain": _write({**proc, "enable_support": "0"}, OUT / f"process_{args.layer}.json"),
        # The CLI has no way to restrict supports to just the hook bores
        # (paint-on in the GUI), so the lid's time is slightly overstated --
        # conservative for the comparison.
        "support": _write({**proc, "enable_support": "1"}, OUT / f"process_{args.layer}_s.json"),
    }

    total_t = total_g = 0.0
    print(f"slice report: {PROCESS[args.layer]}, {FILAMENT}")
    print(f"  {'part':<10}{'time':>8}{'grams':>9}   v1 time   v1 g")
    for stl in stls:
        t, g = slice_part(stl, args.layer, prof)
        total_t, total_g = total_t + t, total_g + g
        base = BASELINE.get(stl.stem)
        ref = f"   {_fmt(base[0]):>7}{base[1]:7.1f}" if base else ""
        print(f"  {stl.stem:<10}{_fmt(t):>8}{g:9.1f}{ref}")
    v1_t = sum(BASELINE[n][0] * c for n, c in BASELINE_COUNT.items())
    v1_g = sum(BASELINE[n][1] * c for n, c in BASELINE_COUNT.items())
    print(f"  {'total':<10}{_fmt(total_t):>8}{total_g:9.1f}   {_fmt(v1_t):>7}{v1_g:7.1f}")
    if not args.stls:
        print(f"  v2 set vs v1 set: time {100 * (total_t / v1_t - 1):+.0f} %, "
              f"filament {100 * (total_g / v1_g - 1):+.0f} %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
