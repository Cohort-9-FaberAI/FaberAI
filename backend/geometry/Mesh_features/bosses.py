from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Boss


NORMAL_CHANGE_THRESHOLD = 0.2
MIN_CYLINDER_FACES = 10



def find_cylindrical_patches(graph: nx.Graph):
    """
    Find connected curved regions in STL mesh.

    Cylindrical surfaces appear as regions where
    triangle normals continuously change.
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
    Estimate cylinder properties from mesh patch.
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

    axis /= np.linalg.norm(axis)



    distances = []


    for point in points:

        projection = (
            np.dot(
                point - center,
                axis
            )
            * axis
        )


        radial = (
            point
            - center
            - projection
        )


        distances.append(
            np.linalg.norm(radial)
        )



    radius = np.mean(
        distances
    )


    return {
        "axis": axis,
        "center": center,
        "radius": float(radius)
    }





def estimate_boss_height(graph, patch, cylinder):
    """
    Estimate boss height along cylinder axis.
    """

    axis = cylinder["axis"]
    center = cylinder["center"]

    projections = []


    for face_id in patch:

        face_center = np.asarray(
            graph.nodes[face_id]["centroid"]
        )


        projections.append(
            np.dot(
                face_center - center,
                axis
            )
        )


    if not projections:
        return 0.0


    return float(
        max(projections) - min(projections)
    )





def is_boss_candidate(graph, patch, cylinder):
    """
    Boss normals point away from cylinder axis.
    """

    axis = cylinder["axis"]
    center = cylinder["center"]

    outward_votes = 0


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



        # normal away from axis = boss
        if np.dot(normal, radial) > 0:

            outward_votes += 1



    ratio = outward_votes / len(patch)


    return ratio > 0.5





def detect_mesh_bosses(mesh, graph: nx.Graph) -> list[Boss]:
    """
    Detect cylindrical bosses from STL mesh.
    """

    bosses = []


    cylindrical_regions = find_cylindrical_patches(
        graph
    )


    boss_id = 0


    for region in cylindrical_regions:


        cylinder = fit_cylinder_to_patch(
            graph,
            region
        )


        if cylinder is None:
            continue



        if not is_boss_candidate(
            graph,
            region,
            cylinder
        ):
            continue



        outer_diameter = (
            cylinder["radius"]
            * 2
        )


        height = estimate_boss_height(
            graph,
            region,
            cylinder
        )



        bosses.append(
            Boss(
                id=boss_id,
                outer_diameter=float(outer_diameter),
                inner_diameter=None,
                wall_thickness=None,
                height=height,
                axis=cylinder["axis"],
                attached_face=None,
                draft_angle=None,
                fillet_radius=None,
                faces=region,
            )
        )


        boss_id += 1



    return bosses
