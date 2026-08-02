from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Hole


NORMAL_CHANGE_THRESHOLD = 0.2
MIN_CYLINDER_FACES = 10



def find_curved_patches(graph: nx.Graph):
    """
    Find connected curved regions in STL mesh.

    Cylindrical walls (holes/bosses) should appear as regions
    where triangle normals continuously change.
    """

    visited = set()
    patches = []


    for node in graph.nodes:

        if node in visited:
            continue


        patch = []
        queue = [node]

        visited.add(node)


        while queue:

            current = queue.pop()

            patch.append(current)


            current_normal = np.asarray(
                graph.nodes[current]["normal"]
            )


            for neighbour in graph.neighbors(current):

                if neighbour in visited:
                    continue


                neighbour_normal = np.asarray(
                    graph.nodes[neighbour]["normal"]
                )


                angle = np.arccos(
                    np.clip(
                        np.dot(
                            current_normal,
                            neighbour_normal
                        ),
                        -1,
                        1
                    )
                )


                if angle > NORMAL_CHANGE_THRESHOLD:

                    visited.add(neighbour)
                    queue.append(neighbour)



        if len(patch) >= MIN_CYLINDER_FACES:
            patches.append(patch)



    return patches





def fit_cylinder_to_patch(graph, patch):
    """
    Estimate cylinder parameters from a curved mesh patch.

    Returns:
        axis
        center
        radius
    """


    points = []


    for face_id in patch:

        centroid = graph.nodes[face_id]["centroid"]

        points.append(
            np.asarray(centroid)
        )


    points = np.asarray(points)


    if len(points) < 5:
        return None



    center = np.mean(
        points,
        axis=0
    )


    centered = points - center


    covariance = np.cov(
        centered.T
    )


    eigenvalues, eigenvectors = np.linalg.eigh(
        covariance
    )


    axis_index = np.argmin(
        eigenvalues
    )


    axis = eigenvectors[:, axis_index]

    axis = axis / np.linalg.norm(axis)



    distances = []


    for point in points:

        projection = (
            np.dot(
                point - center,
                axis
            )
            * axis
        )


        radial_vector = (
            point
            - center
            - projection
        )


        distances.append(
            np.linalg.norm(radial_vector)
        )



    radius = np.mean(distances)


    return {
        "axis": axis,
        "center": center,
        "radius": float(radius)
    }





def estimate_cylinder_depth(graph, patch, cylinder):
    """
    Estimate cylindrical feature depth along cylinder axis.
    """

    axis = cylinder["axis"]
    center = cylinder["center"]

    projections = []


    for face_id in patch:

        face_center = np.asarray(
            graph.nodes[face_id]["centroid"]
        )


        projection = np.dot(
            face_center - center,
            axis
        )


        projections.append(
            projection
        )


    if not projections:
        return 0.0


    return float(
        max(projections) - min(projections)
    )





def classify_hole_type(mesh, patch):
    """
    Classify STL cylindrical feature as through or blind.

    Returns:
        type, through
    """

    boundary_edges = []


    for face_id in patch:

        triangle = mesh.faces[face_id]

        edges = [
            tuple(sorted((triangle[0], triangle[1]))),
            tuple(sorted((triangle[1], triangle[2]))),
            tuple(sorted((triangle[2], triangle[0])))
        ]


        boundary_edges.extend(edges)



    edge_count = {}


    for edge in boundary_edges:

        if edge not in edge_count:
            edge_count[edge] = 0

        edge_count[edge] += 1



    open_edges = [
        edge
        for edge, count in edge_count.items()
        if count == 1
    ]



    if len(open_edges) == 0:

        return "blind", False



    if len(open_edges) > 2:

        return "through", True



    return "blind", False





def is_hole_candidate(graph, patch, cylinder):
    """
    Decide whether a cylindrical patch is a hole.

    Hole:
        normals point towards the cylinder axis

    Boss:
        normals point away from the axis
    """


    axis = cylinder["axis"]
    center = cylinder["center"]


    inward_votes = 0


    for face_id in patch:


        face_center = np.asarray(
            graph.nodes[face_id]["centroid"]
        )


        normal = np.asarray(
            graph.nodes[face_id]["normal"]
        )


        radial = face_center - center


        radial = (
            radial
            - np.dot(radial, axis)
            * axis
        )


        if np.linalg.norm(radial) < 1e-8:
            continue


        radial /= np.linalg.norm(radial)



        if np.dot(normal, radial) < 0:

            inward_votes += 1



    ratio = inward_votes / len(patch)


    return ratio > 0.5





def detect_mesh_holes(mesh, graph: nx.Graph) -> list[Hole]:
    """
    Detect holes from STL mesh.
    """

    holes = []


    curved_regions = find_curved_patches(
        graph
    )


    hole_id = 0


    for region in curved_regions:


        cylinder = fit_cylinder_to_patch(
            graph,
            region
        )


        if cylinder is None:
            continue



        if not is_hole_candidate(
            graph,
            region,
            cylinder
        ):
            continue



        diameter = (
            cylinder["radius"]
            * 2
        )


        depth = estimate_cylinder_depth(
            graph,
            region,
            cylinder
        )


        hole_type, through = classify_hole_type(
            mesh,
            region
        )



        holes.append(
            Hole(
                id=hole_id,
                type=hole_type,
                diameter=float(diameter),
                depth=depth,
                axis=cylinder["axis"],
                center=cylinder["center"],
                through=through,
                cylindrical_faces=region,
                bottom_face=None,
                entry_face=None,
                secondary_diameter=None,
                secondary_depth=None,
            )
        )


        hole_id += 1



    return holes
