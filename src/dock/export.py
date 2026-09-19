from pathlib import Path
from build123d import Part, export_stl, export_step


def write_all(part: Part, name: str, out_dir: Path = Path("out")) -> list[Path]:
    """Write STL (for the slicer) and STEP (for CAD) for `part`. Returns the paths written.

    No 3MF: build123d\x27s Mesher output is valid but Snapmaker Orca reports
    "no geometry data" on it, so the slicer files are the STLs.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stl = out_dir / f"{name}.stl"
    step = out_dir / f"{name}.step"
    export_stl(part, str(stl))
    export_step(part, str(step))
    return [stl, step]
