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
        surface_type = (
            SurfaceType[surface_type_str.upper()]
            if surface_type_str.upper() in SurfaceType.__members__
            else SurfaceType.UNKNOWN
        )

        centroid = attrs.get("centroid")
        normal = attrs.get("normal")
        surface_detail = attrs.get("surface", {})

        # Pull typed geometry params out of the surface detail dict so they
        # land on the Face model's dedicated fields (radius, axis, origin).
        radius = surface_detail.get("radius")
        axis_dir = surface_detail.get("axis_direction")
        axis_loc = surface_detail.get("axis_location") or surface_detail.get("center")

        face = Face(
            id=node_id,
            area=float(attrs.get("area", 0.0)),
            centroid=np.array(centroid) if centroid else np.zeros(3),
            normal=np.array(normal) if normal else np.zeros(3),
            surface_type=surface_type,
            radius=float(radius) if radius is not None else None,
            axis=np.array(axis_dir) if axis_dir is not None else None,
            origin=np.array(axis_loc) if axis_loc is not None else None,
            adjacent_faces=[n for n in face_graph.neighbors(node_id)],
            raw=attrs.get("face"),
        )
        faces_list.append(face)
    
    # Convert edges (graph edges) to Edge objects.
    # build_face_graph stores start_point / end_point on the edge when
    # available; fall back to zeros when they were not captured.
    for edge_id, (u, v, attrs) in enumerate(face_graph.edges(data=True)):
        start_raw = attrs.get("start_point")
        end_raw = attrs.get("end_point")

        curve_type_str = attrs.get("curve_type", "unknown").upper()
        curve_type = (
            CurveType[curve_type_str]
            if curve_type_str in CurveType.__members__
            else CurveType.UNKNOWN
        )

        edge = Edge(
            id=edge_id,
            length=float(attrs.get("edge_length", 0.0)),
            curve_type=curve_type,
            start_point=np.array(start_raw) if start_raw is not None else np.zeros(3),
            end_point=np.array(end_raw) if end_raw is not None else np.zeros(3),
            adjacent_faces=(u, v),
            convex=attrs.get("convex"),
            dihedral_angle=float(attrs.get("angle", 0.0)),
        )
        edges_list.append(edge)
    
    return faces_list, edges_list
