from dataclasses import dataclass, field
import math
import numpy as np


@dataclass
class Fillet:
    """A rounded (convex) blend feature between two adjacent faces."""

    id: int
    radius: float
    length: float                      # approx run length of the blend
    axis: np.ndarray                   # cylinder axis direction of the blend
    center: np.ndarray                 # a point on the axis, mid-run
    cylindrical_face: int              # Face.id of the fillet surface itself
    adjacent_faces: list = field(default_factory=list)   # Face.id values blended together
    convex: bool = True                # fillets are convex (boss-like) blends
    edge_faces: list = field(default_factory=list)        # Face.id values bounding the blend, if more than two

    def arc_length(self, sweep_deg: float = 90.0) -> float:
        """Approximate developed (flattened) length of the blend surface for
        a given sweep angle, defaulting to a quarter-round (90 deg) fillet."""
        return math.radians(sweep_deg) * self.radius

    def surface_area(self, sweep_deg: float = 90.0) -> float:
        """Approximate area of the blend surface, treating it as a partial
        cylinder of the given sweep angle running the full `length`."""
        return self.arc_length(sweep_deg) * self.length

    def aspect_ratio(self) -> float:
        """length : radius — a high ratio flags a long, thin blend run."""
        if self.radius == 0:
            return float("inf")
        return self.length / self.radius
