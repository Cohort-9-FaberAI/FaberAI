from dataclasses import dataclass, field
from typing import Any, Optional
import numpy as np

from .bounding_box import BoundingBox
from .enums import SurfaceType


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

    # Native geometry (TopoDS_Face / build123d Face)
    # raw = None was missing a type annotation, so Face(..., raw=...) crashed immediately with unexpected keyword argument. 
    # This silently broke face_extraction.graph_to_faces_and_edges() for anyone actually using it
    raw: Any = field(default=None, repr=False)

    def is_planar(self):
        return self.surface_type == SurfaceType.PLANE

    def is_cylindrical(self):
        return self.surface_type == SurfaceType.CYLINDER
