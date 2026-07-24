"""GeometryModel — the populated result object for a loaded CAD part."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from .bounding_box import BoundingBox
from .edge import Edge
from .enums import SourceFormat
from .face import Face
from .mesh_quality import MeshQuality
from .wall_sample import WallSample


@dataclass
class GeometryModel:
    """The populated result object for a loaded CAD part.

    Mirrors the "Outputs" section of the spec:
        bounding_box, oriented_bbox, volume_mm3,
        surface_area_mm2, center_mass, moment_of_inertia
    """

    source_format: SourceFormat
    source_path: str

    bounding_box: Optional[BoundingBox] = None
    oriented_bbox: Optional[BoundingBox] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    center_mass: Optional[np.ndarray] = None
    moment_of_inertia: Optional[np.ndarray] = None  # 3x3, about center of mass

    # Cylindrical manufacturing features (populated by geometry.features.*)
    holes: list = field(default_factory=list)
    bosses: list = field(default_factory=list)
    cavities: list = field(default_factory=list)

    # False when the source mesh has holes/damage that couldn't be
    # auto-repaired — volume_mm3 (and to a lesser extent center_mass)
    # should NOT be trusted for DFM scoring when this is False.
    # Always True for STEP/OCC parts, since exact B-rep solids don't
    # have this failure mode the way meshes do.
    measurements_reliable: bool = True

    # Native object (TopoDS_Shape for STEP, trimesh.Trimesh for STL),
    # kept so later pipeline stages (DFM checks, 3D highlighting) can
    # still reach into the original geometry.
    raw: Any = field(default=None, repr=False)

    # Additional data structures for the faces, edges, and wall samples of the model.
    faces: list[Face] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    wall_samples: list[WallSample] = field(default_factory=list)
    nominal_wall: Optional[float] = None
    face_graph: Optional[dict[int, list[int]]] = None

    # Wall thickness statistics (populated by compute_wall_thickness_occ/mesh)
    # Imported lazily to avoid circular imports at the type-hint level.
    wall_thickness_stats: Optional[Any] = None  # WallThicknessStats

    # Mesh quality flags (STL path only; None for STEP)
    mesh_quality: Optional[MeshQuality] = None

    # Print orientation analysis for the 6 candidate axes
    # Imported lazily to avoid circular imports at the type-hint level.
    print_orientations: Optional[Any] = None  # PrintOrientationAnalysis

    def as_dict(self) -> dict:
        """Flat, JSON-friendly summary — handy for API responses/tests."""
        return {
            "source_format": self.source_format.value,
            "source_path": self.source_path,
            "bounding_box": {
                "min": self.bounding_box.min_corner.tolist(),
                "max": self.bounding_box.max_corner.tolist(),
                "width": self.bounding_box.width,
                "depth": self.bounding_box.depth,
                "height": self.bounding_box.height,
            }
            if self.bounding_box
            else None,
            "oriented_bbox": {
                "min": self.oriented_bbox.min_corner.tolist(),
                "max": self.oriented_bbox.max_corner.tolist(),
            }
            if self.oriented_bbox
            else None,
            "volume_mm3": self.volume_mm3,
            "surface_area_mm2": self.surface_area_mm2,
            "measurements_reliable": self.measurements_reliable,
            "center_mass": self.center_mass.tolist()
            if self.center_mass is not None
            else None,
            "moment_of_inertia": self.moment_of_inertia.tolist()
            if self.moment_of_inertia is not None
            else None,
            "num_holes": len(self.holes),
            "num_bosses": len(self.bosses),
            "num_cavities": len(self.cavities),
        }