"""Moment of inertia calculations.

Feeds the P4 aspect-ratio / tall-thin stability check per the DFM spec
(Part 3.1: "Volume, surface area, and center of mass / inertia for
stability reasoning").
"""

from __future__ import annotations

import numpy as np


def _inertia_modules():
    try:
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop

        return GProp_GProps, brepgprop.VolumeProperties
    except (ImportError, ModuleNotFoundError):
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp

        return GProp_GProps, BRepGProp.VolumeProperties_s


def compute_moment_inertia_occ(shape_occ) -> np.ndarray:
    """3x3 inertia matrix (about the center of mass) of a TopoDS_Shape."""
    GProp_GProps, volume_properties = _inertia_modules()

    props = GProp_GProps()
    volume_properties(shape_occ, props)
    mat = props.MatrixOfInertia()
    return np.array([[mat.Value(i, j) for j in range(1, 4)] for i in range(1, 4)])


def compute_moment_inertia_mesh(mesh) -> np.ndarray:
    """3x3 inertia tensor (about the center of mass) of a trimesh.Trimesh.

    Only meaningful for a watertight mesh, same caveat as volume —
    check reliability.is_mesh_reliable() first for anything derived
    from this.
    """
    return np.asarray(mesh.moment_inertia)
