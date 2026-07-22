from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Boss:
    """A cylindrical protrusion (boss) rising from a face."""

    id: int
    outer_diameter: float
    inner_diameter: Optional[float]  # set if the boss is hollow (a tube-like boss)
    wall_thickness: Optional[float]  # (outer - inner) / 2, if hollow
    height: float
    axis: np.ndarray
    attached_face: Optional[int] = None  # Face.id of the face it rises from
    draft_angle: Optional[float] = None  # degrees, if detectable
    fillet_radius: Optional[float] = None

    faces: list = field(default_factory=list)  # Face.id values making up the boss

    def is_solid(self) -> bool:
        return self.inner_diameter is None

    def height_ratio(self) -> float:
        """height : outer_diameter — a high ratio flags a fragile/unstable boss."""
        if self.outer_diameter == 0:
            return float("inf")
        return self.height / self.outer_diameter