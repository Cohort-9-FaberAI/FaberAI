"""Bounding box calculations — axis-aligned and oriented."""

from __future__ import annotations

import numpy as np

from geometry.models import BoundingBox


def compute_bbox_occ(shape) -> BoundingBox:
    """Axis-aligned bounding box of a TopoDS_Shape via Bnd_Box/BRepBndLib."""
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib

    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return BoundingBox(
        min_corner=np.array([xmin, ymin, zmin]),
        max_corner=np.array([xmax, ymax, zmax]),
    )


def compute_bbox_mesh(mesh) -> BoundingBox:
    """Axis-aligned bounding box of a trimesh.Trimesh."""
    bounds = mesh.bounds  # shape (2, 3): [min_xyz, max_xyz]
    return BoundingBox(min_corner=bounds[0], max_corner=bounds[1])


def compute_oriented_bbox_mesh(mesh) -> BoundingBox:
    """Oriented (minimum-volume) bounding box — mesh-only.

    OCC has no first-class equivalent used by this spec, so oriented
    bounding boxes are only produced for the trimesh/STL path.
    """
    obb = mesh.bounding_box_oriented
    extents = obb.primitive.extents
    half = extents / 2.0
    return BoundingBox(
        min_corner=-half,
        max_corner=half,
        transform=np.asarray(obb.primitive.transform),
    )