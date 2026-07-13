"""Surface area calculations."""

from __future__ import annotations


def compute_surface_area_occ(shape) -> float:
    """Surface area of a TopoDS_Shape via BRepGProp.SurfaceProperties."""
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop

    props = GProp_GProps()
    brepgprop.SurfaceProperties(shape, props)
    return float(props.Mass())


def compute_surface_area_mesh(mesh) -> float:
    """Total surface area of a trimesh.Trimesh."""
    return float(mesh.area)