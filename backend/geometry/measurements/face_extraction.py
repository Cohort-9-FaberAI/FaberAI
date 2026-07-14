import numpy as np


def extract_faces_mesh(mesh):
  face_indices_array = mesh.faces
  return np.array(face_indices_array), np.array(mesh.vertices)

def extract_faces_occ(shape):
  vertices, indices = shape.tessellate(tolerance=0.1)

  np_vertices = np.array([tuple(v) for v in vertices])
  np_indices = np.array(indices)

  return np_vertices, np_indices

# face extraction gives an array of the vertex locations and the indices of
# those vertex locations (to save memory)
# example: vertices_array[face_indices_array[face_number]]

def graph_to_faces_and_edges(face_graph, vertices_array, face_indices_array):
    """
    Convert the face_graph NetworkX output to Face and Edge objects.
    
    Args:
        face_graph: NetworkX graph from build_face_graph()
        vertices_array: vertex coords array (for bounding boxes)
        face_indices_array: face triangle indices (for per-face bbox)
    
    Returns:
        (faces_list, edges_list)
    """
    from geometry.models.face import Face
    from geometry.models.edge import Edge
    from geometry.models.enums import SurfaceType, CurveType
    
    faces_list = []
    edges_list = []
    
    # Convert nodes (faces) to Face objects
    for node_id, attrs in face_graph.nodes(data=True):
        surface_type_str = attrs.get("surface_type", "UNKNOWN").lower()
        surface_type = SurfaceType[surface_type_str.upper()] if surface_type_str.upper() in SurfaceType.__members__ else SurfaceType.UNKNOWN
        
        centroid = attrs.get("centroid")
        normal = attrs.get("normal")
        
        face = Face(
            id=node_id,
            area=float(attrs.get("area", 0.0)),
            centroid=np.array(centroid) if centroid else np.zeros(3),
            normal=np.array(normal) if normal else np.zeros(3),
            surface_type=surface_type,
            adjacent_faces=[n for n in face_graph.neighbors(node_id)],
            raw=attrs.get("face"),
        )
        faces_list.append(face)
    
    # Convert edges (graph edges) to Edge objects
    for u, v, attrs in face_graph.edges(data=True):
        edge = Edge(
            id=len(edges_list),
            length=float(attrs.get("edge_length", 0.0)),
            curve_type=CurveType.UNKNOWN,  # can be refined later
            start_point=np.zeros(3),  # would need edge geometry to compute
            end_point=np.zeros(3),
            adjacent_faces=(u, v),
            convex=attrs.get("convex"),
            dihedral_angle=float(attrs.get("angle", 0.0)),
        )
        edges_list.append(edge)
    
    return faces_list, edges_list
