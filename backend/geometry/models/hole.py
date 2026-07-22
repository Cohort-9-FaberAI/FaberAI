from dataclasses import dataclass, field
from typing import Optional
import math
import numpy as np


@dataclass
class Hole:
    """A cylindrical hole feature (through, blind, counterbore, or countersink)."""

    id: int
    type: str  # "through" | "blind" | "counterbore" | "countersink"
    diameter: float
    depth: float
    axis: np.ndarray
    center: np.ndarray
    through: bool

    cylindrical_faces: list = field(default_factory=list)   # Face.id values
    bottom_face: Optional[int] = None                       # Face.id, if capped
    entry_face: Optional[int] = None                        # Face.id at the opening

    # Only populated for counterbore/countersink holes: the secondary
    # feature's own diameter/depth (e.g. the wider counterbore recess,
    # or the countersink cone's included angle via its own radius/depth).
    secondary_diameter: Optional[float] = None
    secondary_depth: Optional[float] = None

    def volume_removed(self) -> float:
        """Approximate material removed, treating the hole as one cylinder
        of this diameter/depth (ignores counterbore/countersink steps —
        callers wanting exact multi-stage volume should sum stages
        separately using secondary_diameter/secondary_depth)."""
        radius = self.diameter / 2.0
        return math.pi * radius ** 2 * self.depth

    def aspect_ratio(self) -> float:
        """depth : diameter — a high ratio flags a hard-to-drill/mold feature."""
        if self.diameter == 0:
            return float("inf")
        return self.depth / self.diameter