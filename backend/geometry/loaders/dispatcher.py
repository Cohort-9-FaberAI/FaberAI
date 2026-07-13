from __future__ import annotations

import os

from geometry.models import GeometryModel, SourceFormat
from geometry.measurements import (
    compute_bbox_occ,
    compute_bbox_mesh,
    compute_oriented_bbox_mesh,
    compute_volume_occ,
    compute_volume_mesh,
    compute_surface_area_occ,
    compute_surface_area_mesh,
    compute_center_mass_occ,
    compute_center_mass_mesh,
    compute_moment_inertia_occ,
    compute_moment_inertia_mesh,
    is_mesh_reliable,
)
from .step_loader_pythonocc import load_step

from .stl_loader_trimesh import load_stl


STEP_EXTENSIONS = {".step", ".stp"}
STL_EXTENSIONS = {".stl"}


def get_file_format(path: str) -> SourceFormat:
    """Determine SourceFormat from a file's extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in STEP_EXTENSIONS:
        return SourceFormat.STEP
    elif ext in STL_EXTENSIONS:
        return SourceFormat.STL
    raise ValueError(
        f"Unsupported file extension '{ext}' for {path}. "
        f"Expected one of {STEP_EXTENSIONS | STL_EXTENSIONS}."
    )


def load_geometry(path: str) -> GeometryModel:
    """Load a STEP or STL file and populate a fully-measured GeometryModel.

    Dispatches on extension:
        .step / .stp -> pythonOCC path
        .stl         -> trimesh path (Daniel's stl_loader.py if present)
    """
    fmt = get_file_format(path)

    if fmt == SourceFormat.STEP:
        shape = load_step(path)
        model = GeometryModel(
            source_format=SourceFormat.STEP, source_path=path, raw=shape
        )
        model.bounding_box = compute_bbox_occ(shape)
        model.oriented_bbox = None  # not produced on the OCC path (see measurements)
        model.volume_mm3 = compute_volume_occ(shape)
        model.surface_area_mm2 = compute_surface_area_occ(shape)
        model.center_mass = compute_center_mass_occ(shape)
        model.moment_of_inertia = compute_moment_inertia_occ(shape)
        return model

    else:  # SourceFormat.STL
        mesh = load_stl(path)
        model = GeometryModel(
            source_format=SourceFormat.STL, source_path=path, raw=mesh
        )
        model.bounding_box = compute_bbox_mesh(mesh)
        model.oriented_bbox = compute_oriented_bbox_mesh(mesh)
        model.volume_mm3 = compute_volume_mesh(mesh)  # attempts repair in-place
        model.surface_area_mm2 = compute_surface_area_mesh(mesh)
        model.center_mass = compute_center_mass_mesh(mesh)
        model.moment_of_inertia = compute_moment_inertia_mesh(mesh)
        model.measurements_reliable = is_mesh_reliable(mesh)  # check AFTER repair
        return model