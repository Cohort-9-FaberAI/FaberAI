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
        .stl         -> trimesh path
    """
    fmt = get_file_format(path)

    if fmt == SourceFormat.STEP:
        return _load_step(path)
    else:
        return _load_stl(path)


# ---------------------------------------------------------------------------
# STEP / OCC path
# ---------------------------------------------------------------------------

def _load_step(path: str) -> GeometryModel:
    shape = load_step(path)
    model = GeometryModel(
        source_format=SourceFormat.STEP, source_path=path, raw=shape
    )

    # Core measurements
    model.bounding_box = compute_bbox_occ(shape)
    model.oriented_bbox = None  # not produced on the OCC path
    model.volume_mm3 = compute_volume_occ(shape)
    model.surface_area_mm2 = compute_surface_area_occ(shape)
    model.center_mass = compute_center_mass_occ(shape)
    model.moment_of_inertia = compute_moment_inertia_occ(shape)

    # Topology: faces, edges, face graph
    try:
        from geometry.measurements.face_extraction import (
            extract_faces_occ,
            graph_to_faces_and_edges,
        )
        from geometry.measurements.face_graph import build_face_graph

        vertices, indices = extract_faces_occ(shape)
        face_graph = build_face_graph(shape.faces(), shape)
        faces_list, edges_list = graph_to_faces_and_edges(face_graph, vertices, indices)

        model.faces = faces_list
        model.edges = edges_list
        model.face_graph = {
            node: list(face_graph.neighbors(node))
            for node in face_graph.nodes()
        }
    except Exception as e:
        print(f"Warning: face/edge extraction failed for {path}: {e}")
        model.faces = []
        model.edges = []
        model.face_graph = None

    # Wall thickness sampling
    try:
        from geometry.measurements.wall_thickness import compute_wall_thickness_occ
        samples, stats = compute_wall_thickness_occ(shape)
        model.wall_samples = samples
        model.wall_thickness_stats = stats
        model.nominal_wall = stats.median_wall if stats else None
    except Exception as e:
        print(f"Warning: wall thickness (OCC) failed for {path}: {e}")

    # Print orientation analysis (requires faces to be populated)
    if model.faces:
        try:
            from geometry.measurements.print_orientations import compute_print_orientations
            model.print_orientations = compute_print_orientations(model.faces)
        except Exception as e:
            print(f"Warning: print orientation analysis failed for {path}: {e}")

    return model


# ---------------------------------------------------------------------------
# STL / trimesh path
# ---------------------------------------------------------------------------

def _load_stl(path: str) -> GeometryModel:
    mesh = load_stl(path)
    model = GeometryModel(
        source_format=SourceFormat.STL, source_path=path, raw=mesh
    )

    # Core measurements
    model.bounding_box = compute_bbox_mesh(mesh)
    model.oriented_bbox = compute_oriented_bbox_mesh(mesh)
    model.volume_mm3 = compute_volume_mesh(mesh)   # attempts repair in-place
    model.surface_area_mm2 = compute_surface_area_mesh(mesh)
    model.center_mass = compute_center_mass_mesh(mesh)
    model.moment_of_inertia = compute_moment_inertia_mesh(mesh)
    model.measurements_reliable = is_mesh_reliable(mesh)  # check AFTER repair

    # Mesh quality flags
    try:
        from geometry.models.mesh_quality import check_mesh_quality
        model.mesh_quality = check_mesh_quality(mesh)
    except Exception as e:
        print(f"Warning: mesh quality check failed for {path}: {e}")

    # Wall thickness sampling
    try:
        from geometry.measurements.wall_thickness import compute_wall_thickness_mesh
        samples, stats = compute_wall_thickness_mesh(mesh)
        model.wall_samples = samples
        model.wall_thickness_stats = stats
        model.nominal_wall = stats.median_wall if stats else None
    except Exception as e:
        print(f"Warning: wall thickness (mesh) failed for {path}: {e}")

    # Face normals from trimesh as lightweight Face objects for orientation analysis
    try:
        from geometry.measurements.print_orientations import compute_print_orientations
        from geometry.models.face import Face
        from geometry.models.enums import SurfaceType
        import numpy as np

        face_normals = mesh.face_normals          # (M, 3)
        face_areas = mesh.area_faces              # (M,)
        centroids = mesh.vertices[mesh.faces].mean(axis=1)  # (M, 3)

        pseudo_faces = [
            Face(
                id=i,
                area=float(face_areas[i]),
                centroid=centroids[i],
                normal=face_normals[i],
                surface_type=SurfaceType.UNKNOWN,
            )
            for i in range(len(face_normals))
        ]
        model.print_orientations = compute_print_orientations(pseudo_faces)
    except Exception as e:
        print(f"Warning: print orientation analysis failed for {path}: {e}")

    return model
