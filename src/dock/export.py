from pathlib import Path
from build123d import Part, Mesher, export_stl, export_step


def write_all(part: Part, name: str, out_dir: Path = Path("out")) -> list[Path]:
    """Write STL, 3MF and STEP for `part`. Returns the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stl = out_dir / f"{name}.stl"
    threemf = out_dir / f"{name}.3mf"
    step = out_dir / f"{name}.step"
    export_stl(part, str(stl))
    m = Mesher()
    m.add_shape(part)
    m.write(str(threemf))
    export_step(part, str(step))
    return [stl, threemf, step]
