"""Center of mass calculations."""

from __future__ import annotations

import numpy as np


def _center_mass_modules():
    try:
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop

        return GProp_GProps, brepgprop.VolumeProperties
    except (ImportError, ModuleNotFoundError):
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp

        return GProp_GProps, BRepGProp.VolumeProperties_s


def compute_center_mass_occ(shape_occ) -> np.ndarray:
    """Center of mass of a solid TopoDS_Shape (volume-weighted centroid)."""
    GProp_GProps, volume_properties = _center_mass_modules()

    props = GProp_GProps()
    volume_properties(shape_occ, props)
    pnt = props.CentreOfMass()
    return np.array([pnt.X(), pnt.Y(), pnt.Z()])


def compute_center_mass_mesh(mesh) -> np.ndarray:
    """Center of mass of a trimesh.Trimesh (volume-weighted for watertight
    meshes; trimesh falls back to an area-weighted estimate otherwise)."""
    return np.asarray(mesh.center_mass)
