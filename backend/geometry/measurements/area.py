"""Surface area calculations — OCP for STEP, trimesh for STL.

See bbox.py for why the STEP path uses OCP, not OCC.Core.
"""

from __future__ import annotations


def _unwrap(shape):
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def compute_surface_area_occ(shape) -> float:
    """Surface area of a build123d Shape via OCP's GProp_GProps."""
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp

    topo_shape = _unwrap(shape)
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(topo_shape, props)
    return float(props.Mass())


def compute_surface_area_mesh(mesh) -> float:
    """Total surface area of a trimesh.Trimesh."""
    return float(mesh.area)