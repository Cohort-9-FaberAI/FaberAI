from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import numpy as np


class SurfaceType(str, Enum):
    PLANE = "plane"
    CYLINDER = "cylinder"
    CONE = "cone"
    SPHERE = "sphere"
    TORUS = "torus"
    BSPLINE = "bspline"
    OTHER = "other"


@dataclass
class FaceInfo:
    """Per-face payload -- mirrors what build_face_graph currently stuffs
    into graph.add_node(i, ...) as separate kwargs.
    """

    index: int
    surface_type: SurfaceType
    area: float
    centroid: np.ndarray
    normal: np.ndarray
    surface: dict = field(default_factory=dict)

    # Native TopoDS_Face / build123d Face, kept for later pipeline stages
    # (DFM checks, 3D highlighting) -- same role as `raw` on GeometryModel.
    raw: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.centroid = np.asarray(self.centroid, dtype=float)
        self.normal = np.asarray(self.normal, dtype=float)

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "surface_type": self.surface_type.value
            if isinstance(self.surface_type, SurfaceType)
            else self.surface_type,
            "area": self.area,
            "centroid": self.centroid.tolist(),
            "normal": self.normal.tolist(),
            "surface": self.surface,
        }


@dataclass
class EdgeInfo:
    """Per-edge payload -- mirrors the kwargs currently passed to
    graph.add_edge(id1, id2, ...).
    """

    face_a: int
    face_b: int
    edge_length: float
    angle: float
    convex: Optional[bool] = None

    def as_dict(self) -> dict:
        return {
            "face_a": self.face_a,
            "face_b": self.face_b,
            "edge_length": self.edge_length,
            "angle": self.angle,
            "convex": self.convex,
        }


@dataclass
class FaceGraphModel:
    """Populated result object for a face-adjacency graph.

    Same shape as GeometryModel: typed summary fields plus a `raw`
    escape hatch to the underlying networkx.Graph for anything the
    flat dataclasses don't expose.
    """

    source_path: str
    faces: list[FaceInfo] = field(default_factory=list)
    adjacencies: list[EdgeInfo] = field(default_factory=list)

    raw: Any = field(default=None, repr=False)  # networkx.Graph

    def as_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "faces": [f.as_dict() for f in self.faces],
            "adjacencies": [e.as_dict() for e in self.adjacencies],
            "num_faces": len(self.faces),
            "num_adjacencies": len(self.adjacencies),
        }

    @classmethod
    def from_networkx(cls, graph, source_path: str = "") -> "FaceGraphModel":
        """Build a FaceGraphModel from the graph produced by build_face_graph."""
        faces = [
            FaceInfo(
                index=i,
                surface_type=data.get("surface_type", SurfaceType.OTHER),
                area=data["area"],
                centroid=data["centroid"],
                normal=data["normal"],
                surface=data.get("surface", {}),
                raw=data.get("face"),
            )
            for i, data in graph.nodes(data=True)
        ]
        adjacencies = [
            EdgeInfo(
                face_a=u,
                face_b=v,
                edge_length=data["edge_length"],
                angle=data["angle"],
                convex=data.get("convex"),
            )
            for u, v, data in graph.edges(data=True)
        ]
        return cls(source_path=source_path, faces=faces, adjacencies=adjacencies, raw=graph)

# example:
'''
# Access a single face by index (list, so positional)
first_face = face_graph_model.faces[0]
print(first_face.surface_type)   # SurfaceType.CYLINDER
print(first_face.area)           # 1710.14
print(first_face.centroid)       # np.array([x, y, z])
print(first_face.normal)         # np.array([nx, ny, nz])
print(first_face.raw)            # the original build123d Face object

# Access an edge/adjacency
first_edge = face_graph_model.adjacencies[0]
print(first_edge.face_a, first_edge.face_b)  # 0, 117
print(first_edge.angle, first_edge.convex)   # 90.0, True

# Filter, like you would with a list of dicts
cylinders = [f for f in face_graph_model.faces if f.surface_type == SurfaceType.CYLINDER]
sharp_convex_edges = [e for e in face_graph_model.adjacencies if e.convex and e.angle > 80]

# Look up a face by its graph index (build a dict once if you need random access a lot)
faces_by_index = {f.index: f for f in face_graph_model.faces}
face_42 = faces_by_index[42]

# Get the whole thing as plain JSON-safe dict/primitives (e.g. for an API response or to save to disk)
summary = face_graph_model.as_dict()
summary["faces"][0]["surface_type"]   # "cylinder" (plain string, not enum)
summary["adjacencies"][0]["edge_length"]

# Still have the raw networkx graph if you need graph algorithms (shortest path, connected components, etc.)
import networkx as nx
nx.shortest_path(face_graph_model.raw, source=0, target=42)
'''