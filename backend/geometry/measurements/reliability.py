"""Mesh repair and reliability checks.

Real uploaded STL files aren't guaranteed to be watertight — this module
attempts automatic repair and reports honestly whether the result should
be trusted downstream (see GeometryModel.measurements_reliable).
"""

from __future__ import annotations


def is_mesh_reliable(mesh) -> bool:
    """True if this mesh's volume/area can be trusted.

    A mesh with unrepaired holes or inconsistent winding can produce
    a volume of the wrong magnitude and/or sign — this should be
    surfaced to the caller (and ultimately the user) rather than
    silently trusted. Call this AFTER attempt_mesh_repair() (or after
    compute_volume_mesh(), which calls it internally) to check the
    post-repair state.
    """
    return bool(mesh.is_watertight and mesh.is_winding_consistent)


def attempt_mesh_repair(mesh) -> None:
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