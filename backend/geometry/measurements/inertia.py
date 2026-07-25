"""Moment of inertia calculations — OCP for STEP, trimesh for STL.

See bbox.py for why the STEP path uses OCP, not OCC.Core.
"""

from __future__ import annotations

import numpy as np


def _unwrap(shape):
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def compute_moment_inertia_occ(shape) -> np.ndarray:
    """3x3 inertia matrix (about the center of mass) of a build123d Shape."""
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp

    topo_shape = _unwrap(shape)
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(topo_shape, props)
    mat = props.MatrixOfInertia()
    return np.array([[mat.Value(i, j) for j in range(1, 4)] for i in range(1, 4)])


def compute_moment_inertia_mesh(mesh) -> np.ndarray:
    """3x3 inertia tensor (about the center of mass) of a trimesh.Trimesh."""
    return np.asarray(mesh.moment_inertia)