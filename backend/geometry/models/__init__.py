"""Public API for geometry.models — import from here, not the submodules."""

from .enums import SourceFormat, SurfaceType, CurveType
from .bounding_box import BoundingBox
from .geometry_model import GeometryModel

# New classes added 
from .face import Face
from .edge import Edge
from .wall_sample import WallSample


__all__ = ["SourceFormat", "SurfaceType", "CurveType",
           "BoundingBox", "GeometryModel", 
           "Face", "Edge", "WallSample" ]
