import networkx as nx
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.gp import gp_Pnt, gp_Vec
import numpy as np
from .surface_classifier import classify_surface_occ
from build123d import *

def compute_face_adjacency(shape) -> TopTools_IndexedDataMapOfShapeListOfShape:
  topo_shape = shape.wrapped if hasattr(shape, "wrapped") else shape
  edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
  TopExp.MapShapesAndAncestors_s(topo_shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)
  return edge_face_map


def _match_face_index(topo_face, face_index):
  for idx, face in face_index.items():
    if face.wrapped.IsSame(topo_face):
      return idx
  return None


def _edge_convexity(edge, n1, n2) -> bool:
  try:
    adaptor = BRepAdaptor_Curve(edge)
    t_mid = (adaptor.FirstParameter() + adaptor.LastParameter()) / 2.0
    pnt, tangent = gp_Pnt(), gp_Vec()
    adaptor.D1(t_mid, pnt, tangent)
    if edge.Orientation() == TopAbs_REVERSED:
      tangent.Reverse()
    t_vec = np.array([tangent.X(), tangent.Y(), tangent.Z()])
    t_norm = np.linalg.norm(t_vec)
    if t_norm < 1e-9:
      return None
    t_vec = t_vec / t_norm
    indicator = float(np.dot(np.cross(n1, n2), t_vec))
    return bool(indicator > 0)
  except Exception:
    return None


def build_face_graph(faces, shape=None) -> nx.Graph:
  graph = nx.Graph()
  face_index = {}

  for i, face in enumerate(faces):
    surface_info = classify_surface_occ(face)
    centroid = face.center()
    normal = face.normal_at(centroid)
    graph.add_node(
        i,
        face=face,
        surface_type=surface_info["type"],
        surface=surface_info,
        area=face.area,
        centroid=(centroid.X, centroid.Y, centroid.Z),
        normal=(normal.X, normal.Y, normal.Z),
    )
    face_index[i] = face

  if shape is None:
    return graph

  edge_face_map = compute_face_adjacency(shape)

  for i in range(1, edge_face_map.Extent() + 1):
    edge = TopoDS.Edge_s(edge_face_map.FindKey(i))
    ancestors = list(edge_face_map.FindFromIndex(i))

    if len(ancestors) != 2:
      continue

    face1_topo = TopoDS.Face_s(ancestors[0])
    face2_topo = TopoDS.Face_s(ancestors[1])

    id1 = _match_face_index(face1_topo, face_index)
    id2 = _match_face_index(face2_topo, face_index)
    if id1 is None or id2 is None or id1 == id2 or graph.has_edge(id1, id2):
      continue

    b123_edge = Edge(edge)
    edge_length = b123_edge.length
    midpoint = b123_edge.position_at(0.5)

    n1 = face_index[id1].normal_at(midpoint)
    n2 = face_index[id2].normal_at(midpoint)
    n1v = np.array([n1.X, n1.Y, n1.Z])
    n2v = np.array([n2.X, n2.Y, n2.Z])

    cosang = float(np.clip(np.dot(n1v, n2v), -1.0, 1.0))
    angle_deg = float(np.degrees(np.arccos(cosang)))
    convex = _edge_convexity(edge, n1v, n2v)

    graph.add_edge(
        id1, id2,
        edge_length=edge_length,
        angle=angle_deg,
        convex=convex,
    )

  return graph

# example: build_face_graph(shape.faces(), shape)