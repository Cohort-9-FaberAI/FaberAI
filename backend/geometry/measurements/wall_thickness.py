"""Wall thickness sampling via ray casting.

Two implementations:
    compute_wall_thickness_occ(shape)  -> STEP/B-rep via pythonOCC
    compute_wall_thickness_mesh(mesh)  -> STL/trimesh

Both return a list[WallSample] and a WallThicknessStats summary.
The strategy is identical for both kernels:
  1. Collect candidate sample points (face centroids for OCC, triangle
     centroids for mesh).
  2. From each point cast a ray in the inward-normal direction.
  3. Find the first intersection with the opposite wall.
  4. The ray length is the local wall thickness at that point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from geometry.models.wall_sample import WallSample


# ---------------------------------------------------------------------------
# Stats dataclass
# ---------------------------------------------------------------------------

@dataclass
class WallThicknessStats:
    """Aggregate statistics over all wall thickness samples."""

    minimum_wall: float       # mm — thinnest measured wall
    maximum_wall: float       # mm — thickest measured wall
    mean_wall: float          # mm — arithmetic mean
    median_wall: float        # mm — median
    # Per-sample thickness values in the same order as the WallSample list.
    # Kept as a plain list so it serialises cleanly to JSON.
    wall_thickness_field: list[float]


# ---------------------------------------------------------------------------
# OCC path
# ---------------------------------------------------------------------------

def compute_wall_thickness_occ(shape) -> tuple[list[WallSample], Optional[WallThicknessStats]]:
    """Ray-cast wall thickness sampling for a STEP B-rep shape.

    Uses pythonOCC BRepIntCurveSurface_Inter to cast rays from each face
    centroid inward and find the opposite surface.

    Parameters
    ----------
    shape : build123d.Shape
        The loaded STEP solid.

    Returns
    -------
    (samples, stats)
        samples : list[WallSample]
        stats   : WallThicknessStats or None if no valid samples were found.
    """
    from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir
    from OCP.GeomAbs import GeomAbs_IsOpposite  # noqa: F401 – kept for reference

    samples: list[WallSample] = []
    topo_shape = shape.wrapped if hasattr(shape, "wrapped") else shape
    faces = list(shape.faces())

    for face_idx, face in enumerate(faces):
        try:
            centroid = face.center()
            normal = face.normal_at(centroid)

            # Inward direction = reverse of outward normal
            inward = gp_Dir(-normal.X, -normal.Y, -normal.Z)
            # Offset slightly off the surface to avoid self-intersection
            origin = gp_Pnt(
                centroid.X + normal.X * 1e-4,
                centroid.Y + normal.Y * 1e-4,
                centroid.Z + normal.Z * 1e-4,
            )
            ray = gp_Lin(origin, inward)

            inter = BRepIntCurveSurface_Inter()
            inter.Init(topo_shape, ray, 1e-6)

            best_dist: Optional[float] = None
            best_face_idx: Optional[int] = None

            while inter.More():
                pt = inter.Pnt()
                dist = origin.Distance(pt)
                # Ignore hits that are essentially on the origin surface (<0.01 mm)
                if dist > 0.01:
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        # Try to match hit face back to our face list
                        hit_face = inter.Face()
                        for j, f in enumerate(faces):
                            if f.wrapped.IsSame(hit_face):
                                best_face_idx = j
                                break
                inter.Next()

            if best_dist is not None:
                sample = WallSample(
                    id=len(samples),
                    point=np.array([centroid.X, centroid.Y, centroid.Z]),
                    normal=np.array([normal.X, normal.Y, normal.Z]),
                    thickness=best_dist,
                    face_id=face_idx,
                    opposite_face_id=best_face_idx,
                    ray_length=best_dist,
                    reliable=True,
                )
                samples.append(sample)

        except Exception:
            # A single face failure must not abort the whole scan
            continue

    stats = _compute_stats(samples) if samples else None
    return samples, stats


# ---------------------------------------------------------------------------
# Mesh (trimesh) path
# ---------------------------------------------------------------------------

def compute_wall_thickness_mesh(mesh) -> tuple[list[WallSample], Optional[WallThicknessStats]]:
    """Ray-cast wall thickness sampling for a trimesh mesh.

    Casts a ray from each triangle centroid in the inward-normal direction
    and records the first hit on the opposite side.

    Parameters
    ----------
    mesh : trimesh.Trimesh

    Returns
    -------
    (samples, stats)
        samples : list[WallSample]
        stats   : WallThicknessStats or None if no valid samples were found.
    """
    
    vertices: np.ndarray = mesh.vertices          # (N, 3)
    tri_indices: np.ndarray = mesh.faces          # (M, 3)
    face_normals: np.ndarray = mesh.face_normals  # (M, 3) — unit outward normals

    # Triangle centroids
    centroids: np.ndarray = vertices[tri_indices].mean(axis=1)  # (M, 3)

    # Inward ray origins: nudge 0.1 mm off the surface inward
    OFFSET = 1e-4
    ray_origins = centroids - face_normals * OFFSET   # (M, 3)
    ray_directions = -face_normals                    # (M, 3) inward

    # Batch ray cast
    try:
        hit_locs, ray_indices, tri_hit_indices = mesh.ray.intersects_location(
            ray_origins=ray_origins,
            ray_directions=ray_directions,
            multiple_hits=False,
        )
    except Exception:
        return [], None

    # Map ray index -> (hit_location, hit_triangle)
    ray_to_hit: dict[int, tuple[np.ndarray, int]] = {}
    for loc, ray_idx, tri_idx in zip(hit_locs, ray_indices, tri_hit_indices):
        if ray_idx not in ray_to_hit:
            ray_to_hit[int(ray_idx)] = (loc, int(tri_idx))

    samples: list[WallSample] = []
    for ray_idx, (hit_loc, hit_tri) in ray_to_hit.items():
        origin = ray_origins[ray_idx]
        dist = float(np.linalg.norm(hit_loc - origin))
        if dist < 0.01:  # skip self-hits
            continue
        sample = WallSample(
            id=len(samples),
            point=centroids[ray_idx].copy(),
            normal=face_normals[ray_idx].copy(),
            thickness=dist,
            face_id=int(ray_idx),
            opposite_face_id=hit_tri,
            ray_length=dist,
            reliable=True,
        )
        samples.append(sample)

    stats = _compute_stats(samples) if samples else None
    return samples, stats


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_stats(samples: list[WallSample]) -> WallThicknessStats:
    """Derive aggregate statistics from a list of WallSample objects."""
    thicknesses = np.array([s.thickness for s in samples], dtype=float)
    return WallThicknessStats(
        minimum_wall=float(thicknesses.min()),
        maximum_wall=float(thicknesses.max()),
        mean_wall=float(thicknesses.mean()),
        median_wall=float(np.median(thicknesses)),
        wall_thickness_field=thicknesses.tolist(),
    )
