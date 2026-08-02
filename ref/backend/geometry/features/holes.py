
from __future__ import annotations

import math
from typing import Optional

import numpy as np

from geometry.models import Hole, SurfaceType

AXIS_COLINEAR_TOL = 1e-3   # radians-ish tolerance for "same axis direction"
AXIS_LINE_TOL = 0.5        # mm — max perpendicular distance between two
                           # axis lines to be considered the same hole axis
CAP_AREA_REL_TOL = 0.25    # 25% tolerance matching a cap face's area to pi*r^2
LARGE_FACE_REL_TOL = 3.0   # a neighbor face is "large/exterior" if its area
                           # is at least this many times pi*r^2


def _axis_projection(point: np.ndarray, origin: np.ndarray, axis: np.ndarray) -> float:
    """Signed distance of `point` along `axis`, measured from `origin`."""
    return float(np.dot(point - origin, axis))


def _same_axis(f1, f2) -> bool:
    """True if two cylindrical faces share the same axis line (direction
    parallel, and the lines are coincident within tolerance)."""
    a1, a2 = f1.axis / np.linalg.norm(f1.axis), f2.axis / np.linalg.norm(f2.axis)
    if abs(abs(np.dot(a1, a2)) - 1.0) > AXIS_COLINEAR_TOL:
        return False
    # perpendicular distance between the two axis lines
    diff = f2.origin - f1.origin
    perp = diff - np.dot(diff, a1) * a1
    return float(np.linalg.norm(perp)) < AXIS_LINE_TOL


def _is_hole_face(face) -> bool:
    """A cylindrical face is a HOLE (concave) if its normal points toward
    its own axis line, rather than away from it (which would be a boss)."""
    axis = face.axis / np.linalg.norm(face.axis)
    # radial vector: from the axis line to the face centroid, perpendicular to axis
    to_centroid = face.centroid - face.origin
    radial = to_centroid - np.dot(to_centroid, axis) * axis
    radial_norm = np.linalg.norm(radial)
    if radial_norm < 1e-9:
        return False  # degenerate, can't tell
    radial_dir = radial / radial_norm
    return bool(np.dot(face.normal, radial_dir) < 0)


def _group_coaxial_faces(cylindrical_faces: list) -> list[list]:
    """Group cylindrical faces that share the same axis (for counterbore/
    countersink stacks); each group becomes one Hole candidate."""
    groups: list[list] = []
    used = set()
    for i, f in enumerate(cylindrical_faces):
        if i in used:
            continue
        group = [f]
        used.add(i)
        for j, g in enumerate(cylindrical_faces):
            if j in used:
                continue
            if _same_axis(f, g):
                group.append(g)
                used.add(j)
        groups.append(group)
    return groups


def _faces_by_id(faces: list) -> dict:
    return {f.id: f for f in faces}


def _edges_touching_face(edges: list, face_id: int) -> list:
    return [e for e in edges if face_id in e.adjacent_faces]


def _neighbor_face_ids(group: list, faces_by_id: dict) -> set:
    """External neighbor face ids for a coaxial group (excluding the group's
    own members)."""
    group_ids = {f.id for f in group}
    neighbors = set()
    for f in group:
        neighbors.update(f.adjacent_faces)
    return neighbors - group_ids


def detect_cylindrical_holes(faces: list, edges: Optional[list] = None) -> list:
    """Find coaxial groups of concave cylindrical faces (candidate holes)
    among a shape's faces. Returns groups, not yet classified — see
    classify_hole()/measure_hole() for the next steps, or just use
    detect_holes() for the fully classified result."""
    cylindrical = [f for f in faces if f.is_cylindrical() and f.axis is not None
                   and f.origin is not None]
    hole_faces = [f for f in cylindrical if _is_hole_face(f)]
    return _group_coaxial_faces(hole_faces)


def measure_hole(group: list, faces_by_id: dict, edges: list) -> dict:
    """Compute diameter/depth/axis/center for a coaxial hole group.

    Uses the smallest-radius cylinder in the group as the "primary" bore
    (the through-going/deepest part) for diameter/axis/center; depth spans
    the full group's axis extent (all stages combined).
    """
    primary = min(group, key=lambda f: f.radius)
    axis = primary.axis / np.linalg.norm(primary.axis)
    origin = primary.origin

    projections = []
    for f in group:
        for e in _edges_touching_face(edges, f.id):
            projections.append(_axis_projection(e.start_point, origin, axis))
            projections.append(_axis_projection(e.end_point, origin, axis))

    if not projections:
        depth = 0.0
        center = primary.centroid
    else:
        depth = max(projections) - min(projections)
        mid = (max(projections) + min(projections)) / 2.0
        center = origin + mid * axis

    return {
        "diameter": primary.radius * 2.0,
        "depth": depth,
        "axis": axis,
        "center": center,
        "min_proj": min(projections) if projections else 0.0,
        "max_proj": max(projections) if projections else 0.0,
    }


def classify_hole(group: list, faces_by_id: dict, edges: list, measurement: dict) -> dict:
    """Determine through/blind, bottom_face, entry_face, and (best-effort)
    counterbore/countersink type for a coaxial hole group."""
    neighbor_ids = _neighbor_face_ids(group, faces_by_id)
    radii = sorted({round(f.radius, 6) for f in group})
    primary = min(group, key=lambda f: f.radius)

    bottom_face_id = None
    entry_face_id = None
    hole_type = "through"

    for nid in neighbor_ids:
        nf = faces_by_id.get(nid)
        if nf is None or not nf.is_planar():
            continue
        # is this neighbor roughly perpendicular to the hole axis? (a cap
        # candidate — either the bottom of a blind hole, or the entry face)
        if abs(np.dot(nf.normal, measurement["axis"])) < 0.9:
            continue

        expected_cap_area = math.pi * primary.radius ** 2
        if nf.area <= expected_cap_area * (1 + CAP_AREA_REL_TOL):
            # small, disc-sized face -> this is a blind-hole bottom cap
            bottom_face_id = nid
            hole_type = "blind"
        elif nf.area >= expected_cap_area * LARGE_FACE_REL_TOL:
            # large surrounding stock face -> this is where the hole enters
            entry_face_id = nid

    # Best-effort counterbore: 2+ distinct radii sharing this axis
    secondary_diameter = None
    secondary_depth = None
    if len(radii) > 1:
        hole_type = "counterbore"
        wider = max(group, key=lambda f: f.radius)
        secondary_diameter = wider.radius * 2.0
        wide_proj = [
            _axis_projection(e.start_point, wider.origin, measurement["axis"])
            for e in _edges_touching_face(edges, wider.id)
        ] + [
            _axis_projection(e.end_point, wider.origin, measurement["axis"])
            for e in _edges_touching_face(edges, wider.id)
        ]
        if wide_proj:
            secondary_depth = max(wide_proj) - min(wide_proj)

    # Best-effort countersink: an adjacent conical face at the axis
    for nid in neighbor_ids:
        nf = faces_by_id.get(nid)
        if nf is not None and nf.surface_type == SurfaceType.CONE:
            hole_type = "countersink"
            break

    return {
        "type": hole_type,
        "through": hole_type == "through",
        "bottom_face": bottom_face_id,
        "entry_face": entry_face_id,
        "secondary_diameter": secondary_diameter,
        "secondary_depth": secondary_depth,
    }


def detect_holes(faces: list, edges: list) -> list:
    """Full pipeline: find, measure, and classify every hole in a shape.

    `faces`/`edges` are the lists produced by
    measurements.face_extraction.graph_to_faces_and_edges().
    """
    faces_by_id = _faces_by_id(faces)
    groups = detect_cylindrical_holes(faces, edges)

    holes = []
    for i, group in enumerate(groups):
        measurement = measure_hole(group, faces_by_id, edges)
        classification = classify_hole(group, faces_by_id, edges, measurement)

        holes.append(Hole(
            id=i,
            type=classification["type"],
            diameter=measurement["diameter"],
            depth=measurement["depth"],
            axis=measurement["axis"],
            center=measurement["center"],
            through=classification["through"],
            cylindrical_faces=[f.id for f in group],
            bottom_face=classification["bottom_face"],
            entry_face=classification["entry_face"],
            secondary_diameter=classification["secondary_diameter"],
            secondary_depth=classification["secondary_depth"],
        ))
    return holes