"""Face angle computation utilities."""

from __future__ import annotations
from typing import Iterable
import numpy as np
from geometry.models.face import Face


def compute_face_angles(
    faces: Iterable[Face],
    axis: np.ndarray,
) -> dict[int, float]:
    """
    Compute the angle (in degrees) between each face normal and
    the given build axis.

    Parameters
    ----------
    faces : Iterable[Face]
        Collection of Face objects.
    axis : np.ndarray
        Build direction as a 3D vector.

    Returns
    -------
    dict[int, float]
        Mapping of face_id -> angle (degrees).
    """

    axis = axis / np.linalg.norm(axis)
    face_angles = {}

    for face in faces:
        normal = face.normal / np.linalg.norm(face.normal)
        dot = np.clip(np.dot(normal, axis), -1.0, 1.0)
        angle = np.degrees(np.arccos(dot))
        face_angles[face.id] = angle

    return face_angles
