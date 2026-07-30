from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Chamfer


# -----------------------------
# Detection parameters
# -----------------------------

MIN_CHAMFER_AREA = 1.0          # mm²
MAX_CHAMFER_WIDTH = 8.0         # mm
MIN_CHAMFER_ANGLE = 15.0        # degrees
MAX_CHAMFER_ANGLE = 75.0        # degrees
MIN_NEIGHBOURS = 2

def find_chamfer_candidates(graph: nx.Graph):
    """
    Find small planar mesh faces that may represent chamfers.
    """

    candidates = []

    for node in graph.nodes:

        area = graph.nodes[node]["area"]

        neighbours = list(
            graph.neighbors(node)
        )

        if len(neighbours) < MIN_NEIGHBOURS:
            continue

        neighbour_areas = [
            graph.nodes[n]["area"]
            for n in neighbours
        ]

        if area >= min(neighbour_areas):
            continue

        candidates.append(node)

    return candidates

def measure_mesh_chamfer(graph, face_id):
    """
    Estimate chamfer width and angle.
    """

    area = graph.nodes[face_id]["area"]

    neighbours = list(
        graph.neighbors(face_id)
    )

    longest_edge = 0.0

    neighbour_normals = []


    for neighbour in neighbours:

        edge_length = graph.edges[
            face_id,
            neighbour
        ].get(
            "length",
            0.0
        )

        if edge_length > longest_edge:
            longest_edge = edge_length

        neighbour_normals.append(
            np.asarray(
                graph.nodes[neighbour]["normal"]
            )
        )


    if longest_edge == 0.0:
        width = 0.0
    else:
        width = area / longest_edge


    angle = 0.0

    if len(neighbour_normals) >= 2:

        dot = np.clip(
            np.dot(
                neighbour_normals[0],
                neighbour_normals[1]
            ),
            -1,
            1
        )

        angle = np.degrees(
            np.arccos(dot)
        )


    return {
        "width": float(width),
        "angle": float(angle),
        "adjacent_faces": neighbours,
    }

def classify_mesh_chamfer(measurement):
    """
    Check whether the measured face satisfies chamfer limits.
    """

    width = measurement["width"]
    angle = measurement["angle"]

    if width > MAX_CHAMFER_WIDTH:
        return None

    if angle < MIN_CHAMFER_ANGLE:
        return None

    if angle > MAX_CHAMFER_ANGLE:
        return None

    return {
        "width": width,
        "angle": angle,
        "adjacent_faces": measurement["adjacent_faces"],
    }

def detect_mesh_chamfers(mesh, graph: nx.Graph) -> list[Chamfer]:
    """
    Detect chamfers from an STL mesh.
    """

    chamfers = []

    candidates = find_chamfer_candidates(graph)

    chamfer_id = 0

    for face_id in candidates:

        measurement = measure_mesh_chamfer(
            graph,
            face_id
        )

        result = classify_mesh_chamfer(
            measurement
        )

        if result is None:
            continue

        chamfers.append(
            Chamfer(
                id=chamfer_id,
                width=result["width"],
                angle=result["angle"],
                face=face_id,
                is_conical=False,
                convex=True,
                adjacent_faces=result["adjacent_faces"],
                valid_edge_count=len(result["adjacent_faces"]),
                valid_area_count=len(result["adjacent_faces"]),
            )
        )

        chamfer_id += 1

    return chamfers
