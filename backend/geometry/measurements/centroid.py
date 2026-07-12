"""Center of mass calculations."""

from __future__ import annotations

import numpy as np


def compute_center_mass_occ(shape) -> np.ndarray:
    """Center of mass of a solid TopoDS_Shape (volume-weighted centroid)."""
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop

    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    pnt = props.CentreOfMass()
    return np.array([pnt.X(), pnt.Y(), pnt.Z()])


def compute_center_mass_mesh(mesh) -> np.ndarray:
    """Center of mass of a trimesh.Trimesh (volume-weighted for watertight
    meshes; trimesh falls back to an area-weighted estimate otherwise)."""
    return np.asarray(mesh.center_mass)