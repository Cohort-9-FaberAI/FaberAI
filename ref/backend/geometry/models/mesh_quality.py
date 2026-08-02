"""Mesh quality metrics for trimesh.Trimesh objects.

Metrics help downstream DFM checks identify problematic geometry:
  - degenerate / near-degenerate triangles
  - extreme aspect ratios
  - non-manifold / open-boundary edges
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class MeshQuality:
    """Summary of mesh quality flags for a trimesh.Trimesh object."""

    is_watertight: bool
    is_winding_consistent: bool
    is_volume: bool


def check_mesh_quality(mesh) -> MeshQuality:
    """
    Inspect a trimesh.Trimesh and return its quality flags.

    Parameters
    ----------
    mesh : trimesh.Trimesh
        The mesh to inspect.

    Returns
    -------
    MeshQuality
        Populated quality summary.

    Raises
    ------
    AttributeError
        If ``mesh`` does not expose the expected trimesh properties.
    """
    try:
        return MeshQuality(
            is_watertight=bool(mesh.is_watertight),
            is_winding_consistent=bool(mesh.is_winding_consistent),
            is_volume=bool(mesh.is_volume),
        )
    except AttributeError as exc:
        raise AttributeError(
            f"check_mesh_quality expects a trimesh.Trimesh object; "
            f"got {type(mesh).__name__}. Original error: {exc}"
        ) from exc
