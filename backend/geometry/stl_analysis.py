from __future__ import annotations

import trimesh

from geometry.measurements.face_graph_mesh import build_face_graph

from geometry.Mesh_features import (
    detect_mesh_holes,
    detect_mesh_bosses,
    detect_mesh_ribs,
)


def analyze_stl_mesh(mesh: trimesh.Trimesh):

    # Build triangle adjacency graph
    graph = build_face_graph(mesh)


    # Detect features
    holes = detect_mesh_holes(
        mesh,
        graph
    )

    bosses = detect_mesh_bosses(
        mesh,
        graph
    )

    ribs = detect_mesh_ribs(
        mesh,
        graph
    )


    return {
        "holes": holes,
        "bosses": bosses,
        "ribs": ribs,
    }
