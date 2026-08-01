from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


ZONE_TOLERANCE = 0.05   # dot-product tolerance for classifying a face as
                        # "side wall" (releases regardless of depth,
                        # since it's parallel to the pull direction)
SHADOW_OFFSET = 1e-3    # mm — how far to nudge the ray start off the
                        # surface, to avoid the ray immediately
                        # re-intersecting its own originating face


@dataclass
class FaceZoneResult:
    """Per-face classification for a given pull direction."""
    face_index: int
    zone: str            # "cavity" | "core" | "side"
    shadowed: bool        # True => this face is a stage-1 undercut candidate
    centroid: np.ndarray
    normal: np.ndarray


def classify_face_zone(normal: np.ndarray, pull_direction: np.ndarray,
                        tolerance: float = ZONE_TOLERANCE) -> str:
    """Which mold half naturally releases this face.

    'cavity' -> face points the same general way as the pull direction
                (released by the half that retreats in +pull_direction)
    'core'   -> face points the opposite way (released by the half that
                retreats in -pull_direction)
    'side'   -> face is roughly parallel to the pull direction (near-zero
                dot product) — releases cleanly regardless of depth,
                since the mold simply slides past it either way
    """
    dot = float(np.dot(normal, pull_direction))
    if dot > tolerance:
        return "cavity"
    elif dot < -tolerance:
        return "core"
    else:
        return "side"


def find_undercut_candidate_faces(shape, pull_direction) -> list[FaceZoneResult]:
    """Stage 1: classify every face's mold-half zone, and flag which ones
    are shadowed (a straight-line path out, in that face's own release
    direction, is blocked by more of the part's own material).

    Parameters
    ----------
    shape : build123d.Shape
        The loaded STEP solid.
    pull_direction : array-like, shape (3,)
        The mold-opening axis. Does not need to be pre-normalized.

    Returns
    -------
    list[FaceZoneResult]
        One entry per face. `shadowed=True` entries are the stage-1
        undercut candidates.
    """
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir

    pull_direction = np.asarray(pull_direction, dtype=float)
    pull_direction = pull_direction / np.linalg.norm(pull_direction)

    topo_shape = shape.wrapped if hasattr(shape, "wrapped") else shape
    faces = list(shape.faces())

    results: list[FaceZoneResult] = []

    for face_idx, face in enumerate(faces):
        centroid_pnt = face.center()
        normal_pnt = face.normal_at(centroid_pnt)
        centroid = np.array([centroid_pnt.X, centroid_pnt.Y, centroid_pnt.Z])
        normal = np.array([normal_pnt.X, normal_pnt.Y, normal_pnt.Z])
        normal_unit = normal / np.linalg.norm(normal)

        zone = classify_face_zone(normal_unit, pull_direction)

        if zone == "side":
            # Parallel to the pull direction -> always releases cleanly,
            # regardless of depth. Not a candidate at all.
            results.append(FaceZoneResult(face_idx, zone, False, centroid, normal_unit))
            continue

        # test_direction: the direction THIS face's own mold half retreats.
        # cavity -> +pull_direction, core -> -pull_direction (opposite).
        test_direction = pull_direction if zone == "cavity" else -pull_direction

        try:
            origin_np = centroid + test_direction * SHADOW_OFFSET
            origin = gp_Pnt(origin_np[0], origin_np[1], origin_np[2])
            direction = gp_Dir(test_direction[0], test_direction[1], test_direction[2])
            ray = gp_Lin(origin, direction)

            inter = BRepIntCurveSurface_Inter()
            inter.Init(topo_shape, ray, 1e-6)

            # gp_Lin is an INFINITE bidirectional line -- the intersector
            # finds hits behind the origin too. Only a hit AHEAD of the
            # origin (positive W, the parametric distance along the given
            # direction) counts as "blocking the straight path out".
            shadowed = False
            while inter.More():
                if inter.W() > 1e-6:
                    shadowed = True
                    break
                inter.Next()
        except Exception:
            # If the ray-cast itself fails for this face, don't silently
            # claim "not shadowed" -- flag it so a human can review it,
            # rather than hiding a potential false negative.
            shadowed = None

        results.append(FaceZoneResult(face_idx, zone, bool(shadowed), centroid, normal_unit))

    return results


# ---------------------------------------------------------------------------
# Grouping: connected shadowed faces -> single Undercut features
# ---------------------------------------------------------------------------

def _compute_face_adjacency(shape) -> dict:
    """Map each face index to the set of face indices it shares an edge
    with. Same technique as measurements.face_graph.compute_face_adjacency,
    reimplemented here to keep this module's OCP dependencies self-contained."""
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
    from OCP.TopoDS import TopoDS

    topo_shape = shape.wrapped if hasattr(shape, "wrapped") else shape
    faces = list(shape.faces())

    edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(topo_shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)

    def match_face_index(topo_face):
        for idx, f in enumerate(faces):
            if f.wrapped.IsSame(topo_face):
                return idx
        return None

    adjacency: dict = {i: set() for i in range(len(faces))}
    for i in range(1, edge_face_map.Extent() + 1):
        ancestors = list(edge_face_map.FindFromIndex(i))
        if len(ancestors) != 2:
            continue
        f1 = TopoDS.Face_s(ancestors[0])
        f2 = TopoDS.Face_s(ancestors[1])
        id1, id2 = match_face_index(f1), match_face_index(f2)
        if id1 is not None and id2 is not None and id1 != id2:
            adjacency[id1].add(id2)
            adjacency[id2].add(id1)

    return adjacency


def _connected_components(shadowed_ids: set, adjacency: dict) -> list[list[int]]:
    """Group shadowed face ids into connected components, using adjacency
    restricted to OTHER shadowed faces only (a shadowed face touching a
    non-shadowed one doesn't merge with it)."""
    visited = set()
    components = []

    for start in shadowed_ids:
        if start in visited:
            continue
        component = []
        stack = [start]
        visited.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in adjacency.get(node, ()):
                if neighbor in shadowed_ids and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(component)

    return components


def detect_undercuts(shape, pull_direction) -> list:
    """Full stage-1 pipeline: find shadowed faces, group adjacent ones into
    Undercut features, for a single given pull direction.

    Returns
    -------
    list[Undercut]
    """
    from geometry.models.undercut import Undercut

    pull_direction = np.asarray(pull_direction, dtype=float)
    pull_direction = pull_direction / np.linalg.norm(pull_direction)

    face_results = find_undercut_candidate_faces(shape, pull_direction)
    shadowed_ids = {r.face_index for r in face_results if r.shadowed}

    if not shadowed_ids:
        return []

    adjacency = _compute_face_adjacency(shape)
    components = _connected_components(shadowed_ids, adjacency)

    results_by_id = {r.face_index: r for r in face_results}

    undercuts = []
    for i, component in enumerate(components):
        centroids = np.array([results_by_id[fid].centroid for fid in component])
        center = centroids.mean(axis=0)
        undercuts.append(Undercut(
            id=i,
            pull_direction=pull_direction,
            center=center,
            face_ids=sorted(component),
        ))

    return undercuts