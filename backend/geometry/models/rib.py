from dataclasses import dataclass, field
import numpy as np


@dataclass
class Rib:
    """A thin, long-and-narrow support wall feature, detected as a pair of
    near-parallel, closely-spaced interior planar faces."""

    id: int
    thickness: float                   # distance between the two faces
    length: float                      # approx run length of the rib
    normal: np.ndarray                 # normal of the first face in the pair
    center: np.ndarray                 # midpoint between the two face locations
    face_pair: tuple = field(default_factory=tuple)   # (Face.id, Face.id)
    shared_neighbor_faces: list = field(default_factory=list)   # Face.id values
    # Only populated when this rib was merged from more than one detected
    # antiparallel pair sharing a face (e.g. a rib with multiple segments).
    extra_face_pairs: list = field(default_factory=list)

    def aspect_ratio(self) -> float:
        """length : thickness — high ratio confirms a long, thin rib rather
        than a generic thin wall or boss."""
        if self.thickness == 0:
            return float("inf")
        return self.length / self.thickness

    def volume_estimate(self) -> float:
        """Rough material volume of the rib, treating it as a rectangular
        slab of thickness x length x length (no width data available, so
        this is a coarse, self-consistent estimate for relative comparison
        only — callers with real width data should compute volume directly)."""
        return self.thickness * self.length * self.length
