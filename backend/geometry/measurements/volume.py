"""Volume calculations — OCP for STEP, trimesh for STL.

See bbox.py for why the STEP path uses OCP, not OCC.Core.
"""

from __future__ import annotations

from .reliability import attempt_mesh_repair


def _unwrap(shape):
    return shape.wrapped if hasattr(shape, "wrapped") else shape


def compute_volume_occ(shape) -> float:
    """Volume of a solid build123d Shape via OCP's GProp_GProps."""
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp

    topo_shape = _unwrap(shape)
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(topo_shape, props)
    return float(props.Mass())


def compute_volume_mesh(mesh) -> float:
    """Signed volume of a trimesh.Trimesh (attempts repair in-place first —
    see reliability.is_mesh_reliable() to check whether the result should
    be trusted)."""
    attempt_mesh_repair(mesh)
    return float(mesh.volume)