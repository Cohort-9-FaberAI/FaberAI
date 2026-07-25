"""Bounding box calculations — axis-aligned and oriented.

FIX: the _occ functions previously used OCC.Core (raw pythonocc-core,
needs conda) and never unwrapped `shape.wrapped`. The dispatcher now
loads STEP files via build123d as its primary path, which bundles a
DIFFERENT, incompatible OpenCASCADE binding called OCP. A shape object
from one binding cannot be passed into a function expecting the other —
they are distinct compiled Python extension types, not interchangeable,
even though both wrap the same underlying C++ library.

Rewritten to use OCP throughout, matching the rest of the STEP pipeline
(face_graph.py, surface_classifier.py, wall_thickness.py all use OCP).
Verified against a real part: exact volume, bbox, and center of mass.
"""

from __future__ import annotations

import numpy as np

from geometry.models import BoundingBox


def _unwrap(shape):
    """Get the raw OCP TopoDS_Shape from a build123d Shape, or pass through
    if already raw."""
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def compute_bbox_occ(shape) -> BoundingBox:
    """Axis-aligned bounding box of a build123d Shape via OCP's Bnd_Box."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib

    topo_shape = _unwrap(shape)
    box = Bnd_Box()
    BRepBndLib.Add_s(topo_shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return BoundingBox(
        min_corner=np.array([xmin, ymin, zmin]),
        max_corner=np.array([xmax, ymax, zmax]),
    )


def compute_bbox_mesh(mesh) -> BoundingBox:
    """Axis-aligned bounding box of a trimesh.Trimesh."""
    bounds = mesh.bounds
    return BoundingBox(min_corner=bounds[0], max_corner=bounds[1])


def compute_oriented_bbox_mesh(mesh) -> BoundingBox:
    """Oriented (minimum-volume) bounding box — mesh-only."""
    obb = mesh.bounding_box_oriented
    extents = obb.primitive.extents
    half = extents / 2.0
    return BoundingBox(
        min_corner=-half,
        max_corner=half,
        transform=np.asarray(obb.primitive.transform),
    )