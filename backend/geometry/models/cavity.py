from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Cavity:
    """An internal cavity / pocket (a concave recess not classified as a
    cylindrical hole — e.g. a rectangular pocket milled into a face)."""

    id: int
    volume: float
    depth: float
    opening_face: Optional[int] = None   # Face.id of the face the pocket opens through
    bottom_faces: list = field(default_factory=list)  # Face.id values
    wall_faces: list = field(default_factory=list)     # Face.id values

    opening_area_value: Optional[float] = None  # cached, see opening_area()

    def opening_area(self) -> float:
        """Area of the opening (mouth) of the cavity."""
        return self.opening_area_value if self.opening_area_value is not None else 0.0