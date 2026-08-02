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
from collections import defaultdict
from typing import Optional
import logging

import numpy as np
import trimesh

from geometry.models.wall_sample import WallSample

logger = logging.getLogger(__name__)
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

def compute_wall_thickness_occ(shape_b123) -> tuple[list[WallSample], Optional[WallThicknessStats]]:
    """Ray-cast wall thickness sampling for a STEP B-rep shape.

    Uses build123d BRepIntCurveSurface_Inter to cast rays from each face
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
    #from OCP.TopAbs import TopAbs_REVERSED


   #from OCP.GeomAbs import GeomAbs_IsOpposite  # noqa: F401 – kept for reference

    samples: list[WallSample] = []
    topo_shape = shape_b123.wrapped if hasattr(shape_b123, "wrapped") else shape_b123
    faces = list(shape_b123.faces())

    OFFSET = 1e-4
    MIN_DISTANCE = 0.01

    for face_idx, face in enumerate(faces):
        try:
            centroid = face.center()
            normal = face.normal_at(centroid)
            # Depending on the OCC face orientation, reverse the geometric normal.
            #if face.wrapped.Orientation() == TopAbs_REVERSED:
            #    normal = -normal

            # Inward direction = reverse of outward normal
            #inward = gp_Dir(-normal.X, -normal.Y, -normal.Z)

            # Offset slightly off the surface to avoid self-intersection
            origin = gp_Pnt(
                centroid.X + normal.X * OFFSET,
                centroid.Y + normal.Y * OFFSET,
                centroid.Z + normal.Z * OFFSET,
            )

            # Shoot toward the interior.
            direction = gp_Dir(-normal.X, -normal.Y, -normal.Z)
            ray = gp_Lin(origin, direction)
            #ray = gp_Lin(origin, inward)

            inter = BRepIntCurveSurface_Inter()
            inter.Init(topo_shape, ray, 1e-6)

            best_dist: Optional[float] = None
            best_face_idx: Optional[int] = None

            while inter.More():
                hit_point = inter.Pnt()
                dist = origin.Distance(hit_point)
                # Ignore hits that are essentially on the origin surface (<0.01 mm)
                if dist > MIN_DISTANCE:
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        # Try to match hit face back to our face list
                        hit_face = inter.Face()
                        best_face_idx = None

                        for j, other_face in enumerate(faces):
                            if other_face.wrapped.IsSame(hit_face):
                                best_face_idx = j
                                break
                        #for j, f in enumerate(faces):
                        #    if f.wrapped.IsSame(hit_face):
                        #        best_face_idx = j
                        #        break
                inter.Next()

            if best_dist is None:
                continue

            samples.append(
                WallSample(
                    id=len(samples),
                    point=np.array([centroid.X, centroid.Y, centroid.Z]),
                    normal=np.array([normal.X, normal.Y, normal.Z]),
                    thickness=float(best_dist),
                    face_id=face_idx,
                    opposite_face_id=best_face_idx,
                    ray_length=float(best_dist),
                    reliable=True,
                )
            )  

        except Exception as e:
            logger.warning(
                "Wall thickness failed on face %d/%d: %s",
                face_idx,
                len(faces),
                e,
            )
    logger.info(
        "Wall thickness sampling: %d valid samples out of %d faces.",
        len(samples),
        len(faces),
    )
    stats = _compute_stats(samples) if samples else None
    return samples, stats


# ---------------------------------------------------------------------------
# Mesh (trimesh) path
# ---------------------------------------------------------------------------

def compute_wall_thickness_mesh(
        mesh,
        samples_per_1000_faces: int = 1000,
        min_samples: int = 1000,
        max_samples: int = 10000,
) -> tuple[list[WallSample], Optional[WallThicknessStats]]:
    """
    Estimate wall thickness on an STL mesh using surface sampling.

    Strategy
    --------
      1. Uniformly sample points on the mesh surface.
      2. Use the corresponding face normal.
      3. Cast a ray inward.
      4. Ignore self-intersections.
      5. Keep the first valid opposite-wall hit.

    This produces much more stable results than sampling every triangle
    because it is largely independent of STL tessellation density.
    """
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
    
    mesh = mesh.copy()

    try:
        mesh.update_faces(mesh.unique_faces())
    except Exception as e:
        logger.warning("Failed to remove duplicate faces: %s", e)
    try:
        mesh.update_faces(mesh.nondegenerate_faces())
    except Exception as e:
        logger.warning("Failed to remove degenerate faces: %s", e)

    try:
        mesh.remove_unreferenced_vertices()
    except Exception:
        logger.warning("Failed to remove unreferenced vertices from mesh.")     
        pass

    try:
        mesh.fix_normals()
    except Exception:
        logger.warning("Failed to fix normals on mesh.")      
        pass

    logger.info(
        "Mesh quality: watertight=%s winding=%s volume=%s faces=%d",
        mesh.is_watertight,
        mesh.is_winding_consistent,
        mesh.is_volume,
        len(mesh.faces),
    )

    # ----------------------------------------------------------
    # Determine sample count
    # ----------------------------------------------------------

    sample_count = int(
        np.clip(
            len(mesh.faces) * samples_per_1000_faces / 1000,
            min_samples,
            max_samples,
        )
    )

    # ----------------------------------------------------------
    # Uniform surface sampling
    # ----------------------------------------------------------

    sample_points, sample_face_ids = trimesh.sample.sample_surface_even(
        mesh,
        sample_count,
    )

    normals = mesh.face_normals[sample_face_ids]

    OFFSET = 0.05
    MIN_DISTANCE = 0.01

    ray_origins = sample_points - normals * OFFSET
    ray_directions = -normals


    #vertices: np.ndarray = mesh.vertices          # (N, 3)
    tri_indices: np.ndarray = mesh.faces          # (M, 3)
    #face_normals: np.ndarray = mesh.face_normals  # (M, 3) — unit outward normals

    # Triangle centroids
    #centroids: np.ndarray = vertices[tri_indices].mean(axis=1)  # (M, 3)

    # ----------------------------------------------------------
    # Cast rays
    # ----------------------------------------------------------
    
    try:
        hit_locations, ray_indices, hit_triangles = mesh.ray.intersects_location(
            ray_origins=ray_origins,
            ray_directions=ray_directions,
            multiple_hits=True,
        )
    except Exception as e:
        logger.warning("Ray casting failed: %s", e) 
        return [], None

    # ----------------------------------------------------------
    # Group hits by ray
    # ----------------------------------------------------------

    hits_by_ray = defaultdict(list)

    for hit_loc, ray_idx, tri_idx in zip(
        hit_locations,
        ray_indices,
        hit_triangles,
    ):

        origin = ray_origins[ray_idx]

        distance = np.linalg.norm(hit_loc - origin)

        hits_by_ray[int(ray_idx)].append(
            (
                float(distance),
                hit_loc,
                int(tri_idx),
            )
        )


    # Map ray index -> (hit_location, hit_triangle)
    #ray_to_hit: dict[int, tuple[np.ndarray, int]] = {}
    #for loc, ray_idx, tri_idx in zip(hit_locs, ray_indices, tri_hit_indices):
    #    if ray_idx not in ray_to_hit:
    #        ray_to_hit[int(ray_idx)] = (loc, int(tri_idx))

    # ----------------------------------------------------------
    # Build samples
    # ----------------------------------------------------------

    samples: list[WallSample] = []

    for ray_idx, hits in hits_by_ray.items():
        hits.sort(key=lambda h: h[0])  # sort by distance
        chosen = None
        for distance, hit_loc, tri_idx in hits:
            if distance < MIN_DISTANCE:
                continue
            chosen = (distance, hit_loc, tri_idx)
            break
        if chosen is None:
            continue
        distance, hit_loc, tri_idx = chosen


        #origin = ray_origins[ray_idx]
        #dist = float(np.linalg.norm(hit_loc - origin))
        #if dist < 0.01:  # skip self-hits
        #    continue
        sample = WallSample(
            id=len(samples),
            point=sample_points[ray_idx].copy(),
            normal=normals[ray_idx].copy(),
            thickness=float(distance),
            face_id=int(sample_face_ids[ray_idx]),
            opposite_face_id=int(tri_idx),
            ray_length=float(distance),
            reliable=True,
        )
        samples.append(sample)

    stats = _compute_stats(samples) if samples else None
    logger.info(
        "Wall thickness sampling: %d valid samples out of %d faces.",
        len(samples),
        len(tri_indices),
    )
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
