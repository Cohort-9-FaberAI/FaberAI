from __future__ import annotations

import math
from typing import Optional

import numpy as np

from geometry.models import Rib

MIN_THICKNESS_DEFAULT = 0.5         # mm
MAX_THICKNESS_DEFAULT = 12.0        # mm
MAX_DRAFT_DEG_DEFAULT = 5.0         # degrees off from perfectly antiparallel
MIN_LENGTH_THICKNESS_RATIO_DEFAULT = 4.0
BBOX_EXTERIOR_TOL = 0.5             # mm — face bbox touching the part bbox


def _faces_by_id(faces: list) -> dict:
    return {f.id: f for f in faces}


def _edges_touching_face(edges: list, face_id: int) -> list:
    return [e for e in edges if face_id in e.adjacent_faces]


def _face_bbox(face, edges: list) -> Optional[tuple]:
    """Bounding box (min, max) for a face. Uses Face.bounding_box when
    present; falls back to its bounding edges' endpoints otherwise."""
    if face.bounding_box is not None:
        return face.bounding_box.min_corner, face.bounding_box.max_corner

    points = []
    for e in _edges_touching_face(edges, face.id):
        points.append(e.start_point)
        points.append(e.end_point)
    if not points:
        return None
    pts = np.array(points)
    return pts.min(axis=0), pts.max(axis=0)


def _global_bbox(faces: list, edges: list) -> tuple:
    """Bounding box of the whole shape, built from each face's own
    bounding box where available, falling back to edge endpoints."""
    mins, maxs = [], []
    for f in faces:
        bbox = _face_bbox(f, edges)
        if bbox is None:
            continue
        mins.append(bbox[0])
        maxs.append(bbox[1])
    if mins:
        return np.array(mins).min(axis=0), np.array(maxs).max(axis=0)

    points = []
    for e in edges:
        points.append(e.start_point)
        points.append(e.end_point)
    pts = np.array(points)
    return pts.min(axis=0), pts.max(axis=0)


def _is_exterior_wall(face_bbox, global_bbox, tol: float = BBOX_EXTERIOR_TOL) -> bool:
    if face_bbox is None:
        return False
    f_min, f_max = face_bbox
    g_min, g_max = global_bbox
    return bool(
        np.any(np.abs(f_min - g_min) < tol) or np.any(np.abs(f_max - g_max) < tol)
    )


def _max_edge_length(face, edges: list) -> float:
    touching = _edges_touching_face(edges, face.id)
    if not touching:
        return 0.0
    return max(e.length for e in touching)


def detect_rib_candidate_planes(faces: list, edges: list) -> list:
    """Build the working list of interior (non-exterior-wall) planar faces
    with their location/normal/neighbor info, ready for antiparallel
    pairing. Returns raw dicts, not yet paired — see detect_ribs() for the
    fully classified result."""
    global_bbox = _global_bbox(faces, edges)
    planes = []
    for f in faces:
        if not f.is_planar():
            continue
        bbox = _face_bbox(f, edges)
        planes.append({
            "face": f,
            "location": f.centroid,
            "normal": f.normal / np.linalg.norm(f.normal),
            "neighbor_ids": set(f.adjacent_faces),
            "is_exterior": _is_exterior_wall(bbox, global_bbox),
        })
    return planes


def _pair_is_rib(p1: dict, p2: dict, edges: list, min_dot_limit: float,
                  min_thickness: float, max_thickness: float,
                  min_length_thickness_ratio: float) -> Optional[dict]:
    if p1["is_exterior"] or p2["is_exterior"]:
        return None

    dot_val = float(np.dot(p1["normal"], p2["normal"]))
    if dot_val > min_dot_limit:
        return None  # not antiparallel enough

    vec_between = p2["location"] - p1["location"]
    thickness = abs(float(np.dot(vec_between, p1["normal"])))
    if not (min_thickness <= thickness <= max_thickness):
        return None

    length = (
        _max_edge_length(p1["face"], edges) + _max_edge_length(p2["face"], edges)
    ) / 2.0
    if thickness <= 0 or (length / thickness) < min_length_thickness_ratio:
        return None

    shared_neighbors = p1["neighbor_ids"] & p2["neighbor_ids"]
    if len(shared_neighbors) < 1:
        return None

    return {
        "thickness": thickness,
        "length": length,
        "shared_neighbors": list(shared_neighbors),
    }


def detect_ribs(faces: list, edges: list, min_thickness: float = MIN_THICKNESS_DEFAULT,
                 max_thickness: float = MAX_THICKNESS_DEFAULT,
                 max_draft_deg: float = MAX_DRAFT_DEG_DEFAULT,
                 min_length_thickness_ratio: float = MIN_LENGTH_THICKNESS_RATIO_DEFAULT) -> list:
    """Full pipeline: find every thin, long, near-parallel interior wall
    pair (a rib) in a shape.

    `faces`/`edges` are the lists produced by
    measurements.face_extraction.graph_to_faces_and_edges().
    """
    planes = detect_rib_candidate_planes(faces, edges)
    min_dot_limit = -math.cos(math.radians(max_draft_deg))

    ribs = []
    next_id = 0
    for n in range(len(planes)):
        for m in range(n + 1, len(planes)):
            p1, p2 = planes[n], planes[m]
            result = _pair_is_rib(
                p1, p2, edges, min_dot_limit,
                min_thickness, max_thickness, min_length_thickness_ratio,
            )
            if result is None:
                continue

            center = (p1["location"] + p2["location"]) / 2.0
            ribs.append(Rib(
                id=next_id,
                thickness=result["thickness"],
                length=result["length"],
                normal=p1["normal"],
                center=center,
                face_pair=(p1["face"].id, p2["face"].id),
                shared_neighbor_faces=result["shared_neighbors"],
            ))
            next_id += 1
    return ribs
