import networkx as nx
import numpy as np



def build_face_graph(mesh) -> nx.Graph:
    """
    Build a face adjacency graph from a trimesh.Trimesh.

    Nodes correspond to mesh triangles.

    Node attributes (same schema as OCC version):
        face
        surface_type
        surface
        area
        centroid
        normal

    Edge attributes:
        edge_length
        angle
        convex
        start_point
        end_point
        curve_type
    """

    graph = nx.Graph()

    faces = mesh.faces
    vertices = mesh.vertices

    ####################################################################
    # Nodes
    ####################################################################

    for i in range(len(faces)):
        tri = faces[i]
        pts = vertices[tri]

        centroid = pts.mean(axis=0)

        graph.add_node(
            i,
            face=i,                       # triangle index
            surface_type="unknown",
            surface={},
            area=float(mesh.area_faces[i]),
            centroid=tuple(centroid),
            normal=tuple(mesh.face_normals[i]),
        )

    ####################################################################
    # Edges
    ####################################################################

    adjacency = mesh.face_adjacency
    adjacency_edges = mesh.face_adjacency_edges

    try:
        adjacency_angles = mesh.face_adjacency_angles
    except Exception:
        adjacency_angles = np.zeros(len(adjacency))

    try:
        adjacency_convex = mesh.face_adjacency_convex
    except Exception:
        adjacency_convex = np.full(len(adjacency), None)

    for k, (f1, f2) in enumerate(adjacency):

        edge_vertices = adjacency_edges[k]

        p1 = vertices[edge_vertices[0]]
        p2 = vertices[edge_vertices[1]]

        edge_length = float(np.linalg.norm(p2 - p1))

        graph.add_edge(
            int(f1),
            int(f2),

            edge_length=edge_length,

            angle=float(np.degrees(adjacency_angles[k])),

            convex=(
                bool(adjacency_convex[k])
                if adjacency_convex[k] is not None
                else None
            ),

            start_point=tuple(p1),
            end_point=tuple(p2),

            curve_type="line",
        )

    return graph