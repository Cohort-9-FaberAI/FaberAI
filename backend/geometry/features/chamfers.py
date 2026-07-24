from __future__ import annotations

import math
from typing import Optional

import numpy as np

from geometry.models import Chamfer, SurfaceType

MAX_CHAMFER_WIDTH_DEFAULT = 8.0     # mm — chamfers are narrow strips
MIN_ANGLE_DEG_DEFAULT = 15.0        # bevel angle window, centered ~45 deg
MAX_ANGLE_DEG_DEFAULT = 75.0
MIN_VALID_EDGES = 2                 # must bevel at least 2 neighbors
MIN_VALID_AREAS = 2                 # at least 2 neighbors must be "larger stock"


def _faces_by_id(faces: list) -> dict:
    return {f.id: f for f in faces}


def _edges_touching_face(edges: list, face_id: int) -> list:
    return [e for e in edges if face_id in e.adjacent_faces]


def _edge_between(edges: list, id1: int, id2: int):
    for e in edges:
        if id1 in e.adjacent_faces and id2 in e.adjacent_faces:
            return e
    return None


def _max_edge_length(face, edges: list) -> float:
    touching = _edges_touching_face(edges, face.id)
    if not touching:
        return 0.0
    return max(e.length for e in touching)


def _strip_width(face, edges: list) -> Optional[float]:
    """Average strip width, approximated as area / longest bounding edge —
    a narrow chamfer strip has a small width relative to its run length."""
    length = _max_edge_length(face, edges)
    if length <= 1e-3:
        return None
    return face.area / length


def _concavity(face, neighbor) -> int:
    """-1 if the neighbor sits behind the face's own normal (concave break,
    material removed toward the part), +1 otherwise."""
    to_neighbor = neighbor.centroid - face.centroid
    return -1 if np.dot(face.normal, to_neighbor) < 0 else 1


def detect_chamfer_candidates(faces: list, max_chamfer_width: float = MAX_CHAMFER_WIDTH_DEFAULT) -> list:
    """Find planar/conical faces narrow enough to be chamfer-strip
    candidates. Returns raw Face objects, not yet classified — see
    classify_chamfer(), or just use detect_chamfers() for the fully
    classified result. Needs `edges` too, so width filtering happens in
    classify_chamfer() instead of here; this just filters by surface type."""
    return [f for f in faces if f.surface_type in (SurfaceType.PLANE, SurfaceType.CONE)]


def classify_chamfer(face, faces_by_id: dict, edges: list,
                      min_angle_deg: float, max_angle_deg: float) -> Optional[dict]:
    """Evaluate a candidate face against the chamfer criteria: narrow
    strip width, >=2 neighbors at a beveled edge angle, >=2 neighbors that
    are larger "stock" faces, and consistent concavity across neighbors."""
    width = _strip_width(face, edges)
    if width is None:
        return None

    neighbor_ids = list(face.adjacent_faces)
    if len(neighbor_ids) < MIN_VALID_EDGES:
        return None

    valid_edges = 0
    valid_areas = 0
    concavities = []
    angles = []

    for nid in neighbor_ids:
        neighbor = faces_by_id.get(nid)
        if neighbor is None:
            continue

        edge = _edge_between(edges, face.id, nid)
        angle = edge.dihedral_angle if (edge is not None and edge.dihedral_angle is not None) else 0.0
        angles.append(angle)
        if min_angle_deg <= angle <= max_angle_deg:
            valid_edges += 1

        if neighbor.area > face.area:
            valid_areas += 1

        concavities.append(_concavity(face, neighbor))

    if valid_edges < MIN_VALID_EDGES or valid_areas < MIN_VALID_AREAS:
        return None
    if not concavities or not all(c == concavities[0] for c in concavities):
        return None

    return {
        "width": width,
        "angle": float(np.mean(angles)) if angles else 0.0,
        "adjacent_faces": neighbor_ids,
        "convex": concavities[0] > 0,
        "valid_edge_count": valid_edges,
        "valid_area_count": valid_areas,
    }


def detect_chamfers(faces: list, edges: list, max_chamfer_width: float = MAX_CHAMFER_WIDTH_DEFAULT,
                     min_angle_deg: float = MIN_ANGLE_DEG_DEFAULT,
                     max_angle_deg: float = MAX_ANGLE_DEG_DEFAULT) -> list:
    """Full pipeline: find and classify every chamfer strip in a shape.

    `faces`/`edges` are the lists produced by
    measurements.face_extraction.graph_to_faces_and_edges().
    """
    faces_by_id = _faces_by_id(faces)
    candidates = detect_chamfer_candidates(faces, max_chamfer_width)

    chamfers = []
    next_id = 0
    for face in candidates:
        result = classify_chamfer(face, faces_by_id, edges, min_angle_deg, max_angle_deg)
        if result is None:
            continue
        if result["width"] > max_chamfer_width:
            continue

        chamfers.append(Chamfer(
            id=next_id,
            width=result["width"],
            angle=result["angle"],
            face=face.id,
            is_conical=(face.surface_type == SurfaceType.CONE),
            convex=result["convex"],
            adjacent_faces=result["adjacent_faces"],
            valid_edge_count=result["valid_edge_count"],
            valid_area_count=result["valid_area_count"],
        ))
        next_id += 1
    return chamfers
