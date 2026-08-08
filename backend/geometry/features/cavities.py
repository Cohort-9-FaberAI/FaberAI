from __future__ import annotations

from typing import Optional

import numpy as np

from geometry.models import Cavity

from .holes import _faces_by_id

WALL_PERP_TOL = 0.15   # |dot(wall.normal, bottom.normal)| must be below this
OPENING_PARALLEL_TOL = 0.9  # dot(opening.normal, bottom.normal) must exceed this


def _is_wall_of(bottom, candidate) -> bool:
    return candidate.is_planar() and abs(float(np.dot(candidate.normal, bottom.normal))) < WALL_PERP_TOL


def _is_opening_of(bottom, candidate) -> bool:
    if not candidate.is_planar():
        return False
    if float(np.dot(candidate.normal, bottom.normal)) < OPENING_PARALLEL_TOL:
        return False
    # must sit further along the shared normal than the bottom (recessed check)
    offset = float(np.dot(candidate.centroid - bottom.centroid, bottom.normal))
    return offset > 1e-6


def detect_cavities(faces: list, edges: Optional[list] = None) -> list:
    """Find candidate (bottom, walls, opening) groups for general pockets."""
    faces_by_id = _faces_by_id(faces)
    candidates = []

    for bottom in faces:
        if not bottom.is_planar():
            continue

        neighbor_ids = bottom.adjacent_faces
        walls = [faces_by_id[nid] for nid in neighbor_ids
                 if nid in faces_by_id and _is_wall_of(bottom, faces_by_id[nid])]
        if not walls:
            continue
        wall_ids = {w.id for w in walls}

        # For each wall, the set of its OTHER neighbors (excluding the
        # bottom itself and excluding fellow walls). A genuine pocket
        # floor has every wall converging on the SAME opening face(s) —
        # take the intersection across all walls, not the union, so a
        # face that only looks like a "bottom" from one wall's local
        # perspective (e.g. a real side wall, whose neighbors fan out to
        # many unrelated exterior faces) gets rejected.
        per_wall_candidates = []
        for w in walls:
            others = {nid for nid in w.adjacent_faces
                      if nid != bottom.id and nid not in wall_ids}
            per_wall_candidates.append(others)

        if not per_wall_candidates:
            continue
        consensus_ids = set.intersection(*per_wall_candidates)

        openings = [faces_by_id[nid] for nid in consensus_ids
                    if nid in faces_by_id and _is_opening_of(bottom, faces_by_id[nid])]
        if not openings:
            continue

        candidates.append({"bottom": bottom, "walls": walls, "openings": openings})

    return candidates


def measure_cavity(candidate: dict) -> dict:
    """Depth (bottom-to-opening offset along the shared normal) and a
    volume estimate (prismatic approximation: bottom area * depth —
    exact for straight, non-tapered pocket walls; an underestimate if
    the walls have draft).

    opening_area uses the bottom face's own area as the mouth's
    cross-section (correct for straight/non-draft pockets, where the
    opening and floor are the same shape and size) — NOT the area of
    the surrounding stock face, which includes material far beyond the
    pocket's actual opening.
    """
    bottom = candidate["bottom"]
    openings = candidate["openings"]
    offsets = [float(np.dot(o.centroid - bottom.centroid, bottom.normal)) for o in openings]
    depth = min(offsets) if offsets else 0.0
    opening_area = bottom.area
    volume = bottom.area * depth
    return {"depth": depth, "opening_area": opening_area, "volume": volume}


def detect_cavities_full(faces: list, edges: Optional[list] = None) -> list:
    """Full pipeline: find, measure every general (non-cylindrical) cavity."""
    candidates = detect_cavities(faces, edges)
    cavities = []
    for i, c in enumerate(candidates):
        m = measure_cavity(c)
        cavities.append(Cavity(
            id=i,
            volume=m["volume"],
            depth=m["depth"],
            opening_face=c["openings"][0].id if c["openings"] else None,
            bottom_faces=[c["bottom"].id],
            wall_faces=[w.id for w in c["walls"]],
            opening_area_value=m["opening_area"],
        ))
    return cavities