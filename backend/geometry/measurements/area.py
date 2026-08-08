"""Surface area calculations."""

from __future__ import annotations


def _surface_area_modules():
    try:
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop

        return GProp_GProps, brepgprop.SurfaceProperties
    except (ImportError, ModuleNotFoundError):
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp

        return GProp_GProps, BRepGProp.SurfaceProperties_s


def compute_surface_area_occ(shape_occ) -> float:
    """Surface area of a TopoDS_Shape via BRepGProp.SurfaceProperties."""
    GProp_GProps, surface_properties = _surface_area_modules()

    props = GProp_GProps()
    surface_properties(shape_occ, props)
    return float(props.Mass())


def compute_surface_area_mesh(mesh) -> float:
    """Total surface area of a trimesh.Trimesh."""
    return float(mesh.area)
