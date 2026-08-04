import networkx as nx
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopExp import TopExp
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import (GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse,GeomAbs_BSplineCurve, GeomAbs_BezierCurve,)
from OCP.gp import gp_Pnt, gp_Vec
import numpy as np
from .surface_classifier import classify_surface_occ
from build123d import Edge

def compute_face_adjacency(shape_b123) -> TopTools_IndexedDataMapOfShapeListOfShape:

  topo_shape = shape_b123.wrapped if hasattr(shape_b123, "wrapped") else shape_b123
  edge_face_map = TopTools_IndexedDataMapOfShapeListOfShape()
  TopExp.MapShapesAndAncestors_s(topo_shape, TopAbs_EDGE, TopAbs_FACE, edge_face_map)
  return edge_face_map

  
def _match_face_index(topo_face, face_index):
  for idx, face in face_index.items():
    if face.wrapped.IsSame(topo_face):
      return idx
  return None


def _edge_endpoints_and_curve_type(edge) -> dict:
  """Extract start point, end point, and curve type from a TopoDS_Edge."""
  try:
    adaptor = BRepAdaptor_Curve(edge)
    t_first = adaptor.FirstParameter()
    t_last = adaptor.LastParameter()
    p_start = gp_Pnt()
    p_end = gp_Pnt()
    adaptor.D0(t_first, p_start)
    adaptor.D0(t_last, p_end)

    curve_type_map = {
      GeomAbs_Line: "line",
      GeomAbs_Circle: "circle",
      GeomAbs_Ellipse: "ellipse",
      GeomAbs_BSplineCurve: "spline",
      GeomAbs_BezierCurve: "spline",
    }
    curve_type = curve_type_map.get(adaptor.GetType(), "unknown")

    return {
      "start_point": (p_start.X(), p_start.Y(), p_start.Z()),
      "end_point": (p_end.X(), p_end.Y(), p_end.Z()),
      "curve_type": curve_type,
    }
  except Exception:
    return {"start_point": None, "end_point": None, "curve_type": "unknown"}


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


def _make_point(x, y, z):
  class _Point:
    def __init__(self, x, y, z):
      self.X = x
      self.Y = y
      self.Z = z
  return _Point(x, y, z)


def _face_centroid(face):
  # Prefer the face's native center method when available.
  if hasattr(face, "center"):
    try:
      return face.center()
    except Exception:
      pass

  # Fall back to OCC's surface centroid if the native face center fails.
  try:
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop
    surface_properties = brepgprop.SurfaceProperties
  except (ImportError, ModuleNotFoundError):
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    surface_properties = BRepGProp.SurfaceProperties_s

  try:
    props = GProp_GProps()
    topo_face = face.wrapped if hasattr(face, "wrapped") else face
    surface_properties(topo_face, props)
    centroid = props.CentreOfMass()
    return _make_point(centroid.X(), centroid.Y(), centroid.Z())
  except Exception:
    pass

  # Finally, fall back to the face's bounding box center.
  try:
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBndLib import brepbndlib
  except (ImportError, ModuleNotFoundError):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    brepbndlib = BRepBndLib.Add_s
  else:
    brepbndlib = brepbndlib.Add

  try:
    box = Bnd_Box()
    topo_face = face.wrapped if hasattr(face, "wrapped") else face
    brepbndlib(topo_face, box)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return _make_point((xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0)
  except Exception:
    return None


def _face_normal(face, centroid):
  if centroid is None:
    return _make_point(0.0, 0.0, 0.0)

  try:
    normal = face.normal_at(centroid)
    return normal
  except Exception:
    return _make_point(0.0, 0.0, 0.0)


def build_face_graph(faces, shape_b123=None) -> nx.Graph:
  graph = nx.Graph()
  face_index = {}

  for i, face in enumerate(faces):
    try:
      surface_info = classify_surface_occ(face)
    except Exception:
      surface_info = {"type": "UNKNOWN"}

    centroid = _face_centroid(face)
    normal = _face_normal(face, centroid)

    graph.add_node(
        i,
        face=face,
        surface_type=surface_info.get("type", "UNKNOWN"),
        surface=surface_info,
        area=getattr(face, "area", 0.0),
        centroid=(centroid.X, centroid.Y, centroid.Z)
        if centroid is not None
        else (0.0, 0.0, 0.0),
        normal=(normal.X, normal.Y, normal.Z)
        if normal is not None
        else (0.0, 0.0, 0.0),
    )
    face_index[i] = face

  if shape_b123 is None:
    return graph

  edge_face_map = compute_face_adjacency(shape_b123)

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
    ep = _edge_endpoints_and_curve_type(edge)

    graph.add_edge(
        id1, id2,
        edge_length=edge_length,
        angle=angle_deg,
        convex=convex,
        start_point=ep["start_point"],
        end_point=ep["end_point"],
        curve_type=ep["curve_type"],
    )

  return graph

# example: build_face_graph(shape.faces(), shape)