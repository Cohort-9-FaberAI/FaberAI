from dataclasses import dataclass
from typing import Optional
import numpy as np

from geometry.models.enums import CurveType


@dataclass
class Edge:
    """
    A topological edge connecting two faces.
    """

    id: int

    length: float

    curve_type: CurveType

    start_point: np.ndarray
    end_point: np.ndarray

    tangent: Optional[np.ndarray] = None

    radius: Optional[float] = None

    adjacent_faces: tuple[int, int] = ()

    convex: Optional[bool] = None

    dihedral_angle: Optional[float] = None

    raw=None