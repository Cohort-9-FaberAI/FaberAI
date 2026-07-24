from dataclasses import dataclass, field


@dataclass
class Chamfer:
    """A flat (or conical) beveled-edge feature connecting two or more
    neighboring faces at an angle, rather than a rounded fillet blend."""

    id: int
    width: float                       # narrow-strip width (area / max edge length)
    angle: float                       # representative bevel angle, degrees
    face: int                          # Face.id of the chamfer strip itself
    is_conical: bool = False           # True for a conical countersink-style chamfer
    convex: bool = True                # True if material was removed (convex break)
    adjacent_faces: list = field(default_factory=list)   # Face.id values it connects
    valid_edge_count: int = 0          # neighbors within the bevel-angle tolerance
    valid_area_count: int = 0          # neighbors larger than the chamfer strip itself

    def is_symmetric_45(self, tol_deg: float = 5.0) -> bool:
        """True if this reads as a standard 45-degree chamfer within tolerance."""
        return abs(self.angle - 45.0) <= tol_deg

    def developed_area(self, run_length: float) -> float:
        """Approximate area of the chamfer strip for a given run length,
        useful when re-deriving width from a differently-measured length."""
        return self.width * run_length
