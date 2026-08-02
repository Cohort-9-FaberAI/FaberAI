"""Volume calculations."""

from __future__ import annotations

from .reliability import attempt_mesh_repair


def _volume_modules():
    try:
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop

        return GProp_GProps, brepgprop.VolumeProperties
    except (ImportError, ModuleNotFoundError):
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp

        return GProp_GProps, BRepGProp.VolumeProperties_s


def compute_volume_occ(shape_occ) -> float:
    """Volume of a solid TopoDS_Shape via GProp_GProps/BRepGProp.VolumeProperties."""
    GProp_GProps, volume_properties = _volume_modules()

    props = GProp_GProps()
    volume_properties(shape_occ, props)
    return float(props.Mass())  # "Mass" with unit density == volume


def compute_volume_mesh(mesh) -> float:
    """Signed volume of a trimesh.Trimesh.

    Volume is only mathematically meaningful for a watertight (fully
    sealed, consistently-wound) mesh. Real uploaded STL files are not
    guaranteed to be watertight — attempt automatic repair first;
    callers should check reliability.is_mesh_reliable(mesh) to know
    whether to trust the result.
    """
    attempt_mesh_repair(mesh)
    return float(mesh.volume)
