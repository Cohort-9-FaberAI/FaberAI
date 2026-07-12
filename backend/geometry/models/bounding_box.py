"""BoundingBox dataclass — axis-aligned or oriented."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


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