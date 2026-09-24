"""Shared printability probe: which faces of a part, as it sits on the bed,
point down more steeply than a printer can lay plastic over air."""
import math


def overhang_deg(face) -> float:
    """How far `face` leans past vertical toward facing straight down:
    0 for a wall, 90 for a flat ceiling; negative for a face that looks up."""
    return math.degrees(math.asin(max(-1.0, min(1.0, -face.normal_at().Z))))


def steep_faces(part, limit_deg: float = 45.0) -> list:
    """Every downward face steeper than `limit_deg`, except the bed face."""
    bed = part.bounding_box().min.Z
    return [f for f in part.faces()
            if overhang_deg(f) > limit_deg + 1e-6
            and abs(f.center().Z - bed) > 1e-6]


def span(face) -> float:
    """The longer horizontal side of a face's bounding box: what a bridge
    over it would have to span."""
    s = face.bounding_box().size
    return max(s.X, s.Y)
