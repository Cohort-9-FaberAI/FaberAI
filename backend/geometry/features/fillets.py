from __future__ import annotations

import math
from typing import Optional

import numpy as np

from geometry.models import Fillet, SurfaceType

MAX_FILLET_RADIUS_DEFAULT = 10.0   # mm — fillets are usually small-radius blends
MIN_PLANE_NEIGHBORS = 2            # a fillet blends at least two adjacent faces
MIN_BOUNDING_EDGES = 3             # full (360 deg) cylinders have 2 cap edges;
                                   # a partial-round fillet strip has more


def _faces_by_id(faces: list) -> dict:
    return {f.id: f for f in faces}


def _edges_touching_face(edges: list, face_id: int) -> list:
    return [e for e in edges if face_id in e.adjacent_faces]


def _axis_projection(point: np.ndarray, origin: np.ndarray, axis: np.ndarray) -> float:
    return float(np.dot(point - origin, axis))


def _is_boss_face(face) -> bool:
    """True if a cylindrical face's normal points away from its own axis
    line (convex, material-adding blend) rather than toward it (a hole)."""
    axis = face.axis / np.linalg.norm(face.axis)
    to_centroid = face.centroid - face.origin
    radial = to_centroid - np.dot(to_centroid, axis) * axis
    radial_norm = np.linalg.norm(radial)
    if radial_norm < 1e-9:
        return False
    radial_dir = radial / radial_norm
    return bool(np.dot(face.normal, radial_dir) > 0)


def _planar_neighbor_ids(face, faces_by_id: dict) -> list:
    return [
        nid for nid in face.adjacent_faces
        if faces_by_id.get(nid) is not None and faces_by_id[nid].is_planar()
    ]


def detect_fillet_candidates(faces: list, max_fillet_radius: float = MAX_FILLET_RADIUS_DEFAULT) -> list:
    """Find cylindrical faces that look like convex, small-radius blends
    between (at least) two planar neighbor faces. Returns raw Face objects,
    not yet measured/classified — see measure_fillet()/classify_fillet(),
    or just use detect_fillets() for the fully classified result."""
    faces_by_id = _faces_by_id(faces)
    candidates = []
    for f in faces:
        if not f.is_cylindrical() or f.axis is None or f.origin is None:
            continue
        if f.radius is None or f.radius > max_fillet_radius:
            continue
        if len(_planar_neighbor_ids(f, faces_by_id)) < MIN_PLANE_NEIGHBORS:
            continue
        if not _is_boss_face(f):
            continue
        candidates.append(f)
    return candidates


def measure_fillet(face, edges: list) -> dict:
    """Compute run length/axis/center for a fillet candidate face, using
    the projected span of its bounding edges along the cylinder axis."""
    axis = face.axis / np.linalg.norm(face.axis)
    origin = face.origin

    touching = _edges_touching_face(edges, face.id)
    projections = []
    for e in touching:
        projections.append(_axis_projection(e.start_point, origin, axis))
        projections.append(_axis_projection(e.end_point, origin, axis))

    if not projections:
        length = 0.0
        center = face.centroid
    else:
        length = max(projections) - min(projections)
        mid = (max(projections) + min(projections)) / 2.0
        center = origin + mid * axis

    return {
        "axis": axis,
        "center": center,
        "length": length,
        "bounding_edges": touching,
    }


def classify_fillet(face, faces_by_id: dict, measurement: dict) -> dict:
    """Reject full (360 deg) cylindrical bosses using an edge-count proxy,
    and identify which planar faces this fillet blends together."""
    n_edges = len(measurement["bounding_edges"])
    is_full_cylinder = n_edges < MIN_BOUNDING_EDGES

    plane_neighbors = _planar_neighbor_ids(face, faces_by_id)
    other_neighbors = [
        nid for nid in face.adjacent_faces if nid not in plane_neighbors
    ]

    return {
        "rejected": is_full_cylinder,
        "adjacent_faces": plane_neighbors,
        "edge_faces": other_neighbors,
    }


def detect_fillets(faces: list, edges: list, max_fillet_radius: float = MAX_FILLET_RADIUS_DEFAULT) -> list:
    """Full pipeline: find, measure, and classify every fillet in a shape.

    `faces`/`edges` are the lists produced by
    measurements.face_extraction.graph_to_faces_and_edges().
    """
    faces_by_id = _faces_by_id(faces)
    candidates = detect_fillet_candidates(faces, max_fillet_radius)

    fillets = []
    next_id = 0
    for face in candidates:
        measurement = measure_fillet(face, edges)
        classification = classify_fillet(face, faces_by_id, measurement)
        if classification["rejected"]:
            continue

        fillets.append(Fillet(
            id=next_id,
            radius=face.radius,
            length=measurement["length"],
            axis=measurement["axis"],
            center=measurement["center"],
            cylindrical_face=face.id,
            adjacent_faces=classification["adjacent_faces"],
            convex=True,
            edge_faces=classification["edge_faces"],
        ))
        next_id += 1
    return fillets
