"""Moment of inertia calculations.

Feeds the P4 aspect-ratio / tall-thin stability check per the DFM spec
(Part 3.1: "Volume, surface area, and center of mass / inertia for
stability reasoning").
"""

from __future__ import annotations

import numpy as np


def compute_moment_inertia_occ(shape) -> np.ndarray:
    """3x3 inertia matrix (about the center of mass) of a TopoDS_Shape.

    Reuses the same GProp_GProps/VolumeProperties call as
    compute_center_mass_occ — inertia is populated as a side effect of
    that same volume-properties computation, not a separate query.
    """
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop

    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    mat = props.MatrixOfInertia()
    return np.array([[mat.Value(i, j) for j in range(1, 4)] for i in range(1, 4)])


def compute_moment_inertia_mesh(mesh) -> np.ndarray:
    """3x3 inertia tensor (about the center of mass) of a trimesh.Trimesh.

    Only meaningful for a watertight mesh, same caveat as volume —
    check reliability.is_mesh_reliable() first for anything derived
    from this.
    """
    return np.asarray(mesh.moment_inertia)