from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Rib


NORMAL_TOLERANCE = 0.05
MIN_PATCH_FACES = 5
MIN_ASPECT_RATIO = 5


def _are_opposite_normals(n1, n2):
    """
    Check if two faces face opposite directions.
    """

    n1 = np.asarray(n1)
    n2 = np.asarray(n2)

    return abs(np.dot(n1, n2) + 1) < NORMAL_TOLERANCE



def find_planar_patches(graph: nx.Graph):

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

            current_normal = graph.nodes[current]["normal"]

            for neighbour in graph.neighbors(current):

                if neighbour in visited:
                    continue

                neighbour_normal = graph.nodes[neighbour]["normal"]

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

                if angle < NORMAL_TOLERANCE:
                    visited.add(neighbour)
                    queue.append(neighbour)

        if len(patch) >= MIN_PATCH_FACES:
            patches.append(patch)

    return patches



def patch_center(graph, patch):

    centers = []

    for face_id in patch:
        centers.append(
            np.asarray(
                graph.nodes[face_id]["centroid"]
            )
        )

    return np.mean(
        centers,
        axis=0
    )



def detect_mesh_ribs(mesh, graph: nx.Graph) -> list[Rib]:

    ribs = []

    patches = find_planar_patches(graph)

    rib_id = 0


    for i in range(len(patches)):

        for j in range(i + 1, len(patches)):

            patch_a = patches[i]
            patch_b = patches[j]


            normal_a = graph.nodes[patch_a[0]]["normal"]
            normal_b = graph.nodes[patch_b[0]]["normal"]


            # They must face opposite directions
            if not _are_opposite_normals(
                normal_a,
                normal_b
            ):
                continue


            center_a = patch_center(
                graph,
                patch_a
            )

            center_b = patch_center(
                graph,
                patch_b
            )


            thickness = np.linalg.norm(
                center_b - center_a
            )


            if thickness <= 0:
                continue


            length = max(
                len(patch_a),
                len(patch_b)
            )


            if length / thickness < MIN_ASPECT_RATIO:
                continue


            center = (
                center_a + center_b
            ) / 2


            ribs.append(
                Rib(
                    id=rib_id,
                    thickness=float(thickness),
                    length=float(length),
                    normal=np.asarray(normal_a),
                    center=center,
                    face_pair=(
                        patch_a[0],
                        patch_b[0]
                    ),
                    shared_neighbor_faces=[]
                )
            )

            rib_id += 1


    return ribs
