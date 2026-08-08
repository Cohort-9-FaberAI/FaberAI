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
        Build direction as a 3D vector. Must be non-zero.

    Returns
    -------
    dict[int, float]
        Mapping of face_id -> angle in degrees [0, 180].

    Raises
    ------
    ValueError
        If ``axis`` is a zero vector.
    """
    axis = np.asarray(axis, dtype=float)
    axis_norm = np.linalg.norm(axis)
    if axis_norm < 1e-9:
        raise ValueError("axis must be a non-zero vector.")
    axis = axis / axis_norm

    face_angles: dict[int, float] = {}

    for face in faces:
        normal = np.asarray(face.normal, dtype=float)
        normal_norm = np.linalg.norm(normal)
        if normal_norm < 1e-9:
            # Degenerate face — skip rather than produce nan
            continue
        normal = normal / normal_norm
        dot = np.clip(np.dot(normal, axis), -1.0, 1.0)
        face_angles[face.id] = float(np.degrees(np.arccos(dot)))

    return face_angles
