from dataclasses import dataclass
import numpy as np


@dataclass
class Overhang:
    """A single mesh/graph face whose downward-facing angle exceeds the
    print-support threshold."""

    face_id: int
    centroid: np.ndarray
    normal: np.ndarray
    angle: float
    area: float

    def needs_support(self, angle_threshold: float = 45.0) -> bool:
        """True if this face's angle exceeds the max angle threshold for printing without support."""
        return self.angle > angle_threshold