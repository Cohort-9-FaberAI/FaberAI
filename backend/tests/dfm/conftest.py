"""Shared geometry fixtures for the DFM engine tests.

The payloads here are hand-built rather than produced by the geometry engine so
each test can isolate one rule. They deliberately include **mocked ribs[] and
bosses[]**: the geometry team's feature recognition is still landing, and the
DFM evaluators must work the day it does without an architectural change.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

import pytest

from dfm.config import load_dfm_config


@pytest.fixture(scope="session")
def config():
    return load_dfm_config()


def _vector(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Dict[str, float]:
    return {"x": x, "y": y, "z": z}


@pytest.fixture()
def step_geometry() -> Dict[str, Any]:
    """A clean STEP-like part: 3 mm walls, drafted faces, no defects.

    Faces: 1 and 2 are vertical walls with 2° of draft (normal 88°/92° to the
    pull axis), 3 is the top face.
    """
    return copy.deepcopy({
        "status": "completed",
        "filename": "bracket.stp",
        "source_format": "step",
        "bounding_box": {
            "min": _vector(0, 0, 0),
            "max": _vector(100, 60, 40),
            "width": 100.0, "depth": 60.0, "height": 40.0,
        },
        "volume_mm3": 120000.0,
        "surface_area_mm2": 30000.0,
        "measurements_reliable": True,
        "center_mass": _vector(50, 30, 20),
        "faces": [
            {"id": 1, "area": 10000.0, "centroid": _vector(0, 30, 20),
             "normal": _vector(-1, 0, 0), "surface_type": "plane"},
            {"id": 2, "area": 10000.0, "centroid": _vector(100, 30, 20),
             "normal": _vector(1, 0, 0), "surface_type": "plane"},
            {"id": 3, "area": 10000.0, "centroid": _vector(50, 30, 40),
             "normal": _vector(0, 0, 1), "surface_type": "plane"},
        ],
        "edges": [],
        "face_graph": {1: [2, 3], 2: [1, 3], 3: [1, 2]},
        "wall_samples": [
            {"id": 1, "point": _vector(0, 30, 20), "normal": _vector(-1, 0, 0),
             "thickness": 3.0, "face_id": 1, "ray_length": 3.0, "reliable": True},
            {"id": 2, "point": _vector(0, 20, 20), "normal": _vector(-1, 0, 0),
             "thickness": 3.05, "face_id": 1, "ray_length": 3.05, "reliable": True},
            {"id": 3, "point": _vector(100, 30, 20), "normal": _vector(1, 0, 0),
             "thickness": 2.95, "face_id": 2, "ray_length": 2.95, "reliable": True},
            {"id": 4, "point": _vector(50, 30, 40), "normal": _vector(0, 0, 1),
             "thickness": 3.0, "face_id": 3, "ray_length": 3.0, "reliable": True},
        ],
        "nominal_wall": 3.0,
        "wall_thickness_stats": {
            "minimum_wall": 2.95, "maximum_wall": 3.05,
            "mean_wall": 3.0, "median_wall": 3.0,
            "wall_thickness_field": [3.0, 3.05, 2.95, 3.0],
        },
        "print_orientations": {
            "orientations": [
                {
                    "axis_label": "+Z", "axis": [0.0, 0.0, 1.0],
                    # Faces 1/2 sit 2° off vertical (drafted); face 3 points up.
                    "face_angles": {1: 88.0, 2: 92.0, 3: 0.0},
                    "min_angle": 0.0, "max_angle": 92.0,
                    "mean_angle": 60.0, "median_angle": 88.0,
                    "overhang_area_mm2": 0.0, "overhang_ratio": 0.0,
                },
                {
                    "axis_label": "-Z", "axis": [0.0, 0.0, -1.0],
                    "face_angles": {1: 92.0, 2: 88.0, 3: 180.0},
                    "min_angle": 88.0, "max_angle": 180.0,
                    "mean_angle": 120.0, "median_angle": 92.0,
                    "overhang_area_mm2": 10000.0, "overhang_ratio": 0.33,
                },
            ],
            "recommended": "+Z",
        },
        "holes": [],
        "cavities": [],
        # Feature recognition present and clean.
        "ribs": [],
        "bosses": [],
    })


@pytest.fixture()
def step_geometry_with_features(step_geometry) -> Dict[str, Any]:
    """The same part with mocked rib/boss recognition results attached.

    Rib is 1.5 mm on a 3 mm wall (50% — right at the Minor boundary); boss is
    hollow with a 1.2 mm wall (40%). Tests override these to move the ratio.
    """
    geometry = copy.deepcopy(step_geometry)
    geometry["ribs"] = [
        {
            "id": 1, "thickness": 1.5, "length": 40.0,
            "normal": _vector(0, 1, 0), "center": _vector(50, 30, 10),
            "face_pair": [1, 2], "shared_neighbor_faces": [3], "aspect_ratio": 26.7,
        }
    ]
    geometry["bosses"] = [
        {
            "id": 1, "outer_diameter": 8.0, "inner_diameter": 5.6,
            "wall_thickness": 1.2, "height": 12.0, "axis": _vector(0, 0, 1),
            "center": _vector(30, 30, 20), "attached_face": 3,
            "faces": [4], "is_solid": False, "height_ratio": 1.5,
        }
    ]
    return geometry


@pytest.fixture()
def geometry_without_features(step_geometry) -> Dict[str, Any]:
    """Geometry as the engine ships it *today*: no ribs[]/bosses[] arrays.

    M5 and M6 must report Not assessed on this payload — never a failure, and
    never a score penalty.
    """
    geometry = copy.deepcopy(step_geometry)
    geometry.pop("ribs")
    geometry.pop("bosses")
    return geometry


@pytest.fixture()
def stl_geometry() -> Dict[str, Any]:
    """A tall, thin STL part with thin walls and an enclosed cavity."""
    return copy.deepcopy({
        "status": "completed",
        "filename": "tower.stl",
        "source_format": "stl",
        "bounding_box": {
            "min": _vector(0, 0, 0), "max": _vector(30, 20, 180),
            "width": 30.0, "depth": 20.0, "height": 180.0,
        },
        "volume_mm3": 24000.0,
        "surface_area_mm2": 16000.0,
        "measurements_reliable": True,
        "faces": [],
        "edges": [],
        "wall_samples": [],
        "nominal_wall": 0.9,
        "wall_thickness_stats": {
            "minimum_wall": 0.6, "maximum_wall": 1.4,
            "mean_wall": 0.9, "median_wall": 0.9,
            "wall_thickness_field": [0.6, 0.65, 0.7, 0.9, 1.2, 1.4],
        },
        "mesh_quality": {
            "is_watertight": True, "is_winding_consistent": True, "is_volume": True,
        },
        "print_orientations": {
            "orientations": [
                {
                    "axis_label": "+Z", "axis": [0.0, 0.0, 1.0],
                    "face_angles": {0: 150.0, 1: 90.0, 2: 0.0},
                    "min_angle": 0.0, "max_angle": 150.0,
                    "mean_angle": 80.0, "median_angle": 90.0,
                    "overhang_area_mm2": 4000.0, "overhang_ratio": 0.25,
                },
            ],
            "recommended": "+Z",
        },
        "holes": [],
        "cavities": [
            {
                "id": 1, "volume": 800.0, "depth": 20.0,
                "opening_face": None, "bottom_faces": [], "wall_faces": [],
                "opening_area": 0.0,
            }
        ],
    })


@pytest.fixture()
def empty_geometry() -> Dict[str, Any]:
    """The worst realistic input: a file that parsed but yielded almost nothing.

    Every rule must degrade to Not assessed; nothing may raise.
    """
    return {
        "status": "completed",
        "filename": "broken.stl",
        "source_format": "stl",
        "measurements_reliable": False,
        "mesh_quality": {
            "is_watertight": False, "is_winding_consistent": False, "is_volume": False,
        },
    }
