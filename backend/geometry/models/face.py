from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from backend.geometry.models.bounding_box import BoundingBox
from geometry.models.enums import SurfaceType


@dataclass
class Face:
    """
    A single topological face of the CAD model.

    Represents one TopoDS_Face (STEP) or one segmented surface patch (STL).
    """

    id: int

    # Geometry
    area: float                      # mm²
    centroid: np.ndarray             # (3,)
    normal: np.ndarray               # unit vector

    # Surface classification
    surface_type: SurfaceType

    # Bounding box of the face
    bounding_box: Optional[BoundingBox] = None

    # Principal curvature (optional for STEP, estimated for STL)
    mean_curvature: Optional[float] = None
    gaussian_curvature: Optional[float] = None

    # STEP surface parameters
    radius: Optional[float] = None       # cylinder/sphere/fillet
    axis: Optional[np.ndarray] = None
    origin: Optional[np.ndarray] = None

    # Topology
    adjacent_faces: list[int] = field(default_factory=list)
    edge_ids: list[int] = field(default_factory=list)

    # Native geometry
    raw=None

    def is_planar(self):
        return self.surface_type == SurfaceType.PLANE

    def is_cylindrical(self):
        return self.surface_type == SurfaceType.CYLINDER
