"""
Data models shared by the STEP (pythonOCC) and STL (trimesh) pipelines.

Both loaders/measurement backends populate the SAME shapes defined here,
so downstream DFM checks never need to know which CAD backend produced
a given GeometryModel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np


class SourceFormat(str, Enum):
    STEP = "step"
    STL = "stl"


@dataclass
class BoundingBox:
    """Axis-aligned (or oriented) bounding box.

    min_corner / max_corner are 3-vectors (x, y, z).
    width/depth/height follow the spec's convention:
        width = xmax - xmin
        depth = ymax - ymin
        height = zmax - zmin
    For an *oriented* box, min_corner/max_corner are expressed in the
    box's own local frame, and `transform` (4x4) maps that local frame
    back to world space. `transform` is None for axis-aligned boxes.
    """

    min_corner: np.ndarray
    max_corner: np.ndarray
    transform: Optional[np.ndarray] = None

    @property
    def width(self) -> float:
        return float(self.max_corner[0] - self.min_corner[0])

    @property
    def depth(self) -> float:
        return float(self.max_corner[1] - self.min_corner[1])

    @property
    def height(self) -> float:
        return float(self.max_corner[2] - self.min_corner[2])

    @property
    def extents(self) -> np.ndarray:
        return np.array([self.width, self.depth, self.height])

    def __post_init__(self) -> None:
        # Defensive: always store as float64 numpy arrays, regardless of
        # whether OCC handed us a tuple/list or trimesh handed us an array.
        self.min_corner = np.asarray(self.min_corner, dtype=float)
        self.max_corner = np.asarray(self.max_corner, dtype=float)


@dataclass
class GeometryModel:
    """The populated result object for a loaded CAD part.

    Mirrors the "Outputs" section of the spec:
        bounding_box, oriented_bbox, volume_mm3,
        surface_area_mm2, center_mass
    """

    source_format: SourceFormat
    source_path: str

    bounding_box: Optional[BoundingBox] = None
    oriented_bbox: Optional[BoundingBox] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    center_mass: Optional[np.ndarray] = None
    moment_of_inertia: Optional[np.ndarray] = None  # 3x3, about center of mass

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
        }