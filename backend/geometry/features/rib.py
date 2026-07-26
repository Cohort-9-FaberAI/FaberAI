from dataclasses import dataclass,field
from typing import Optional
import numpy as np

@dataclass
class Rib:
    """A thin reinforcing wall."""
    id: int
    thickness: float
    height: float
    lenght: float
    axis: np.ndarray
    attached_face: Optional[int] = None
    draft_angle: Optional[float] = None
    fillet_radius: Optional[float] = None

    faces: list[int] = field(default_factory=list)

    def aspect_ratio(self) -> float:
        """Height will be divided by thickness."""
        if self.thickness==0:
            return float("inf")
        return self.height/self.thickness
