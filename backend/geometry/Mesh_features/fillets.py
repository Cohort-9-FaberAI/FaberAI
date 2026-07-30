from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Fillet

NORMAL_CHANGE_THRESHOLD = 0.2
MIN_CYLINDER_FACES = 10
MAX_FILLET_RADIUS = 10.0

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
def measure_mesh_fillet(graph, patch, cylinder):
        """
        Estimate fillet length and center along the cylinder axis.
        """

        axis = cylinder["axis"]
        center = cylinder["center"]

        projections = []

        for face_id in patch:

            centroid = np.asarray(
                graph.nodes[face_id]["centroid"]
            )

            projections.append(
                np.dot(
                    centroid - center,
                    axis
                )
            )

        if not projections:

            return {
                "axis": axis,
                "center": center,
                "length": 0.0,
            }

        length = max(projections) - min(projections)

        return {
            "axis": axis,
            "center": center,
            "length": float(length),
        }

def classify_mesh_fillet(cylinder):
    """
    Basic STL fillet classifier.

    Reject cylinders that are too large to reasonably
    represent a fillet.
    """

    if cylinder["radius"] > MAX_FILLET_RADIUS:
        return False

    return True

def detect_mesh_fillets(mesh, graph: nx.Graph) -> list[Fillet]:
    """
    Detect cylindrical fillets from an STL mesh.
    """

    fillets = []

    cylindrical_regions = find_cylindrical_patches(graph)

    fillet_id = 0

    for region in cylindrical_regions:

        cylinder = fit_cylinder_to_patch(
            graph,
            region
        )

        if cylinder is None:
            continue

        if not classify_mesh_fillet(cylinder):
            continue

        measurement = measure_mesh_fillet(
            graph,
            region,
            cylinder
        )

        fillets.append(
            Fillet(
                id=fillet_id,
                radius=float(cylinder["radius"]),
                length=measurement["length"],
                axis=measurement["axis"],
                center=measurement["center"],
                cylindrical_face=region[0],
                adjacent_faces=[],
                convex=True,
                edge_faces=[],
            )
        )

        fillet_id += 1

    return fillets
