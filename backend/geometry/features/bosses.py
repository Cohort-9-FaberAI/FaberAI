from __future__ import annotations

from typing import Optional

import numpy as np

from geometry.models import Boss

from .holes import (
    _axis_projection,
    _same_axis,
    _group_coaxial_faces,
    _faces_by_id,
    _edges_touching_face,
    _neighbor_face_ids,
)


def _is_boss_face(face) -> bool:
    """A cylindrical face is a BOSS (convex) if its normal points away from
    its own axis line — the opposite test from _is_hole_face()."""
    axis = face.axis / np.linalg.norm(face.axis)
    to_centroid = face.centroid - face.origin
    radial = to_centroid - np.dot(to_centroid, axis) * axis
    radial_norm = np.linalg.norm(radial)
    if radial_norm < 1e-9:
        return False
    radial_dir = radial / radial_norm
    return bool(np.dot(face.normal, radial_dir) > 0)


def detect_bosses(faces: list, edges: Optional[list] = None) -> list:
    """Find coaxial groups of convex cylindrical faces (candidate bosses)."""
    cylindrical = [f for f in faces if f.is_cylindrical() and f.axis is not None
                   and f.origin is not None]
    boss_faces = [f for f in cylindrical if _is_boss_face(f)]
    return _group_coaxial_faces(boss_faces)


def find_attached_face(group: list, faces_by_id: dict) -> Optional[int]:
    """The planar face the boss rises from: the largest planar neighbor
    whose normal is roughly parallel to the boss axis (the base plate)."""
    axis = group[0].axis / np.linalg.norm(group[0].axis)
    neighbor_ids = _neighbor_face_ids(group, faces_by_id)

    best_id, best_area = None, 0.0
    for nid in neighbor_ids:
        nf = faces_by_id.get(nid)
        if nf is None or not nf.is_planar():
            continue
        if abs(np.dot(nf.normal, axis)) < 0.9:
            continue  # not perpendicular to the boss axis -> not the base
        if nf.area > best_area:
            best_id, best_area = nid, nf.area
    return best_id


def measure_boss(group: list, faces_by_id: dict, edges: list) -> dict:
    """Compute outer diameter, height, and axis for a boss group."""
    outer = max(group, key=lambda f: f.radius)
    axis = outer.axis / np.linalg.norm(outer.axis)
    origin = outer.origin

    projections = []
    for f in group:
        for e in _edges_touching_face(edges, f.id):
            projections.append(_axis_projection(e.start_point, origin, axis))
            projections.append(_axis_projection(e.end_point, origin, axis))

    height = (max(projections) - min(projections)) if projections else 0.0

    return {
        "outer_diameter": outer.radius * 2.0,
        "height": height,
        "axis": axis,
    }


def detect_bosses_full(faces: list, edges: list, holes: Optional[list] = None) -> list:
    """Full pipeline: find, measure, and classify every boss in a shape.

    If `holes` (from holes.detect_holes()) is provided, a boss whose axis
    coincides with a hole's axis and whose diameter is smaller is treated
    as a hollow/tube-like boss (inner_diameter set from that hole).
    """
    faces_by_id = _faces_by_id(faces)
    groups = detect_bosses(faces, edges)

    bosses = []
    for i, group in enumerate(groups):
        measurement = measure_boss(group, faces_by_id, edges)
        attached = find_attached_face(group, faces_by_id)

        inner_diameter = None
        wall_thickness = None
        if holes:
            for h in holes:
                axis_a = group[0].axis / np.linalg.norm(group[0].axis)
                axis_b = h.axis / np.linalg.norm(h.axis)
                colinear = abs(abs(np.dot(axis_a, axis_b)) - 1.0) < 1e-2
                if colinear and h.diameter < measurement["outer_diameter"]:
                    inner_diameter = h.diameter
                    wall_thickness = (measurement["outer_diameter"] - inner_diameter) / 2.0
                    break

        bosses.append(Boss(
            id=i,
            outer_diameter=measurement["outer_diameter"],
            inner_diameter=inner_diameter,
            wall_thickness=wall_thickness,
            height=measurement["height"],
            axis=measurement["axis"],
            attached_face=attached,
            faces=[f.id for f in group],
        ))
    return bosses