"""Center of mass calculations — OCP for STEP, trimesh for STL.

See bbox.py for why the STEP path uses OCP, not OCC.Core.
"""

from __future__ import annotations

import numpy as np


def _unwrap(shape):
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def compute_center_mass_occ(shape) -> np.ndarray:
    """Center of mass of a solid build123d Shape (volume-weighted centroid)."""
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp

    topo_shape = _unwrap(shape)
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(topo_shape, props)
    pnt = props.CentreOfMass()
    return np.array([pnt.X(), pnt.Y(), pnt.Z()])


def compute_center_mass_mesh(mesh) -> np.ndarray:
    """Center of mass of a trimesh.Trimesh (volume-weighted for watertight
    meshes; trimesh falls back to an area-weighted estimate otherwise)."""
    return np.asarray(mesh.center_mass)