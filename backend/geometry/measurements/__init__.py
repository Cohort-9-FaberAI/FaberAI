"""
Public API for geometry.measurements — import from here, not the submodules.

Each measurement has two implementations:
    compute_<thing>_occ(shape)   -> uses OpenCASCADE (pythonOCC), for STEP
    compute_<thing>_mesh(mesh)   -> uses trimesh, for STL

pythonOCC is imported lazily inside each *_occ function (in its own
submodule) so this package still imports cleanly in environments where
pythonOCC/OpenCASCADE isn't installed.
"""

from .bbox import compute_bbox_occ, compute_bbox_mesh, compute_oriented_bbox_mesh
from .volume import compute_volume_occ, compute_volume_mesh
from .area import compute_surface_area_occ, compute_surface_area_mesh
from .centroid import compute_center_mass_occ, compute_center_mass_mesh
from .inertia import compute_moment_inertia_occ, compute_moment_inertia_mesh
from .reliability import is_mesh_reliable, attempt_mesh_repair
from .faceangles import compute_face_angles
from .wall_thickness import compute_wall_thickness_occ, compute_wall_thickness_mesh, WallThicknessStats
from .print_orientations import compute_print_orientations, PrintOrientationAnalysis, PrintOrientationResult


__all__ = [
    "compute_bbox_occ",
    "compute_bbox_mesh",
    "compute_oriented_bbox_mesh",
    "compute_volume_occ",
    "compute_volume_mesh",
    "compute_surface_area_occ",
    "compute_surface_area_mesh",
    "compute_center_mass_occ",
    "compute_center_mass_mesh",
    "compute_moment_inertia_occ",
    "compute_moment_inertia_mesh",
    "is_mesh_reliable",
    "attempt_mesh_repair",
    "compute_face_angles",
    "compute_wall_thickness_occ",
    "compute_wall_thickness_mesh",
    "WallThicknessStats",
    "compute_print_orientations",
    "PrintOrientationAnalysis",
    "PrintOrientationResult",
]