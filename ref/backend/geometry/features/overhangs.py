from __future__ import annotations

import numpy as np
import networkx as nx

from geometry.models import Overhang

MAX_OVERHANG_ANGLE_DEFAULT = 45.0   # degrees from vertical


def detect_overhangs(face_graph: nx.Graph, max_overhang_angle: float = MAX_OVERHANG_ANGLE_DEFAULT) -> list:
    """Find every face whose normal points down steeply enough to exceed
    max_overhang_angle from vertical, excluding the shape's lowest face/faces. 
    Operates directly on the raw face_graph.
    """
    overhang_faces = []

    global_min_centroid = min(face_graph.nodes(data="centroid"), key=lambda x: x[1][2])

    for node_id, data in face_graph.nodes(data=True):
        if data["normal"][2] < 0.0 and data["centroid"][2] != global_min_centroid[1][2]:
            angle = float(np.degrees(np.arcsin(-data["normal"][2])))

            if angle > max_overhang_angle:
                overhang_faces.append(Overhang(
                    face_id=node_id,
                    centroid=np.array(data["centroid"]),
                    normal=np.array(data["normal"]),
                    angle=angle,
                    area=float(data["area"]),
                ))

    return overhang_faces