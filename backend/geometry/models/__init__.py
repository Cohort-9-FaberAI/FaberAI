"""Public API for geometry.models — import from here, not the submodules."""

from .enums import SourceFormat, SurfaceType, CurveType
from .bounding_box import BoundingBox
from .geometry_model import GeometryModel

# New classes added
from .face import Face
from .edge import Edge
from .wall_sample import WallSample
from .mesh_quality import MeshQuality, check_mesh_quality


__all__ = [
    "SourceFormat", "SurfaceType", "CurveType",
    "BoundingBox", "GeometryModel",
    "Face", "Edge", "WallSample",
    "MeshQuality", "check_mesh_quality",
]