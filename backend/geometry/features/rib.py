from __future__ import annotations

from typing import Optional

import numpy as np

from geometry.models import Rib


PARALLEL_TOL = 1e-3
MAX_RIB_THICKNESS = 5.0  # mm


def _is_rib_face(face) -> bool:
    """
    A rib side is usually a planar face.
    """
    return face.is_planar()

def _are_parallel(face1, face2) -> bool:
    """
    Returns True if the face normals are parallel or anti-parallel.
    """

    n1 = face1.normal / np.linalg.norm(face1.normal)
    n2 = face2.normal / np.linalg.norm(face2.normal)

    return abs(abs(np.dot(n1, n2)) - 1.0) < PARALLEL_TOL

def _face_distance(face1, face2) -> float:
    """
    Perpendicular distance between two parallel faces.
    """

    n = face1.normal / np.linalg.norm(face1.normal)

    return abs(np.dot(face2.centroid - face1.centroid, n))

def _find_parallel_pairs(faces: list) -> list[tuple]:
    """
    Find thin parallel planar face pairs that could represent ribs.
    """

    planar = [f for f in faces if _is_rib_face(f)]

    candidates = []

    for i in range(len(planar)):
        for j in range(i + 1, len(planar)):

            f1 = planar[i]
            f2 = planar[j]

            if not _are_parallel(f1, f2):
                continue

            thickness = _face_distance(f1, f2)

            if thickness > MAX_RIB_THICKNESS:
                continue

            candidates.append((f1, f2, thickness))

    return candidates

def _measure_rib(face1, face2, thickness):
    """
    Estimate rib dimensions from two parallel faces.
    """

    if face1.bounding_box is None or face2.bounding_box is None:
        return None

    bb1 = face1.bounding_box
    bb2 = face2.bounding_box

    # Combined bounding box
    mins = np.minimum(bb1.min_corner, bb2.min_corner)
    maxs = np.maximum(bb1.max_corner, bb2.max_corner)

    dims = maxs - mins

    # Smallest dimension should be the thickness
    dims = sorted(dims)

    return {
        "thickness": thickness,
        "height": dims[2],
        "length": dims[1],
        "axis": face1.normal,
    }


def detect_ribs(faces: list) -> list[Rib]:
    """
    Detect thin reinforcing ribs from planar face pairs.
    """

    candidates = _find_parallel_pairs(faces)

    ribs = []

    for i, (face1, face2, thickness) in enumerate(candidates):

        measurement = _measure_rib(face1, face2, thickness)

        if measurement is None:
            continue

        rib = Rib(
            id=i,
            thickness=measurement["thickness"],
            height=measurement["height"],
            length=measurement["length"],
            axis=measurement["axis"],
            attached_face=None,
            faces=[face1.id, face2.id],
        )

        ribs.append(rib)

    return ribs
