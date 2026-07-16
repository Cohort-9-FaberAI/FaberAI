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
    "This is the summary of the mesh quality"
    is_watertight:bool
    is_winding_consistent:bool
    is_volume:bool

def check_mesh_quality(mesh) -> MeshQuality:
    return MeshQuality(
        is_watertight=mesh.is_watertight,
        is_winding_consistent=mesh.is_winding_consistent,
        is_volume=mesh.is_volume
    )
