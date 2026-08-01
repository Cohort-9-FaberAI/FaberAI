"""Public API for geometry.models — import from here, not the submodules."""

from .enums import SourceFormat, SurfaceType, CurveType
from .bounding_box import BoundingBox
from .geometry_model import GeometryModel

# New classes added
from .face import Face
from .edge import Edge
from .wall_sample import WallSample
from .mesh_quality import MeshQuality, check_mesh_quality
from .hole import Hole
from .boss import Boss
from .cavity import Cavity
from .fillet import Fillet
from .rib import Rib
from .chamfer import Chamfer
from .overhang import Overhang



__all__ = [
    "SourceFormat", "SurfaceType", "CurveType",
    "BoundingBox", "GeometryModel",
    "Face", "Edge", "WallSample",
    "MeshQuality", "check_mesh_quality",
    "Hole", "Boss", "Cavity",
    "Fillet", "Rib", "Chamfer", "Overhang"
]
