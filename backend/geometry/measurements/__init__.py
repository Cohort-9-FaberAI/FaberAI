"""
Global geometric measurements for STEP (pythonOCC) shapes and
STL (trimesh) meshes.

Each measurement has two implementations:
    compute_<thing>_occ(shape)   -> uses OpenCASCADE (pythonOCC)
    compute_<thing>_mesh(mesh)   -> uses trimesh

pythonOCC is imported lazily inside each *_occ function so that this
module can still be imported (and the *_mesh functions used) in
environments where pythonOCC/OpenCASCADE isn't installed.
"""

from __future__ import annotations

import numpy as np

from geometry.models import BoundingBox


# Bounding box
def compute_bbox_occ(shape) -> BoundingBox:
    """Axis-aligned bounding box of a TopoDS_Shape via Bnd_Box/BRepBndLib."""
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib

    box = Bnd_Box()
    brepbndlib.Add(shape, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return BoundingBox(
        min_corner=np.array([xmin, ymin, zmin]),
        max_corner=np.array([xmax, ymax, zmax]),
    )


def compute_bbox_mesh(mesh) -> BoundingBox:
    """Axis-aligned bounding box of a trimesh.Trimesh."""
    bounds = mesh.bounds  # shape (2, 3): [min_xyz, max_xyz]
    return BoundingBox(min_corner=bounds[0], max_corner=bounds[1])


def compute_oriented_bbox_mesh(mesh) -> BoundingBox:
    """Oriented (minimum-volume) bounding box — mesh-only.

    OCC has no first-class equivalent used by this spec, so oriented
    bounding boxes are only produced for the trimesh/STL path.
    """
    obb = mesh.bounding_box_oriented
    # obb.primitive.transform is the 4x4 taking the box's local frame
    # (centered at origin, extents = obb.primitive.extents) to world space.
    extents = obb.primitive.extents
    half = extents / 2.0
    return BoundingBox(
        min_corner=-half,
        max_corner=half,
        transform=np.asarray(obb.primitive.transform),
    )



# Volume
def compute_volume_occ(shape) -> float:
    """Volume of a solid TopoDS_Shape via GProp_GProps/BRepGProp.VolumeProperties."""
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop

    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)
    return float(props.Mass())  # "Mass" with unit density == volume


def compute_volume_mesh(mesh) -> float:
    """Signed volume of a trimesh.Trimesh.

    Volume is only mathematically meaningful for a watertight (fully
    sealed, consistently-wound) mesh. Real uploaded STL files are not
    guaranteed to be watertight — attempt automatic repair first;
    callers should check `is_mesh_reliable(mesh)` to know whether to
    trust the result.
    """
    _attempt_mesh_repair(mesh)
    return float(mesh.volume)


def is_mesh_reliable(mesh) -> bool:
    """True if this mesh's volume/area can be trusted.

    A mesh with unrepaired holes or inconsistent winding can produce
    a volume of the wrong magnitude and/or sign — this should be
    surfaced to the caller (and ultimately the user) rather than
    silently trusted.
    """
    return bool(mesh.is_watertight and mesh.is_winding_consistent)


def _attempt_mesh_repair(mesh) -> None:
    """Best-effort in-place repair: fix winding, then try to patch holes.

    Some real-world STL files have structural damage (missing chunks,
    disconnected pieces) that no amount of repair can fix — in that
    case this simply leaves the mesh as-is, and is_mesh_reliable()
    will correctly report False.
    """
    if mesh.is_watertight and mesh.is_winding_consistent:
        return  # already good, nothing to do

    try:
        mesh.fix_normals()
        if not mesh.is_watertight:
            mesh.fill_holes()
    except Exception:
        # Repair libraries (networkx, etc.) missing or repair itself
        # failed — leave mesh as-is; is_mesh_reliable() will flag it.
        pass



# Surface area
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



# Center of mass
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



# Moment of inertia
# Feeds the P4 aspect-ratio / tall-thin stability check per the DFM spec
# (Part 3.1: "Volume, surface area, and center of mass / inertia for
# stability reasoning").
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
    check is_mesh_reliable() first for anything derived from this.
    """
    return np.asarray(mesh.moment_inertia)