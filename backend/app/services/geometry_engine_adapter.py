"""Adapter layer between the async worker and the geometry engine.

This module defines a response contract that mirrors the geometry data
produced by the geometry package and can be consumed by the Celery worker.
The worker should only ever call `run_geometry_engine`, so the backend can
keep working even if the real geometry engine is swapped later.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from geometry.loaders import load_geometry


# --- Contract schemas for the geometry engine response ---

class Vector3(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    z: float


class BoundingBoxSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: Vector3
    max: Vector3
    width: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None


class FaceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    area: float
    centroid: Vector3
    normal: Vector3
    surface_type: str
    # Typed geometry parameters — populated when surface_type provides them
    radius: Optional[float] = None
    axis: Optional[Vector3] = None
    origin: Optional[Vector3] = None


class EdgeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    length: float
    curve_type: str
    start_point: Vector3
    end_point: Vector3
    dihedral_angle: Optional[float] = None
    convex: Optional[bool] = None


class WallSampleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    point: Vector3
    normal: Vector3
    thickness: float
    face_id: int
    opposite_face_id: Optional[int] = None
    ray_length: float
    reliable: bool = True


class ThreeJSHighlight(BaseModel):
    """Bounding box coordinates for highlighting a region on the 3D canvas."""
    model_config = ConfigDict(extra="forbid")

    type: str = "bounding_box"
    color: str
    min: Vector3
    max: Vector3
    center: Vector3


class GeometryEngineIssue(BaseModel):
    """A single manufacturability issue reported by the geometry engine."""
    model_config = ConfigDict(extra="forbid")

    type: str
    severity: Literal["high", "medium", "low"]
    message: str
    recommendation: str
    three_js_highlight: ThreeJSHighlight


class GeometryEngineResponse(BaseModel):
    """Response shape compatible with the geometry package's GeometryModel."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed"] = "completed"
    filename: str
    manufacturability_score: Optional[float] = Field(default=None, ge=0, le=100)
    mock_score: Optional[float] = Field(default=None, ge=0, le=100)

    source_format: Optional[str] = None
    source_path: Optional[str] = None
    bounding_box: Optional[BoundingBoxSummary] = None
    oriented_bbox: Optional[BoundingBoxSummary] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    measurements_reliable: bool = True
    center_mass: Optional[Vector3] = None
    moment_of_inertia: Optional[List[List[float]]] = None
    faces: List[FaceSummary] = Field(default_factory=list)
    edges: List[EdgeSummary] = Field(default_factory=list)
    wall_samples: List[WallSampleSummary] = Field(default_factory=list)
    nominal_wall: Optional[float] = None
    face_graph: Optional[dict[int, list[int]]] = None
    issues: List[GeometryEngineIssue] = Field(default_factory=list)


def _to_vector3(values: Any) -> Optional[Vector3]:
    if values is None:
        return None
    if isinstance(values, Vector3):
        return values
    arr = list(values)
    if len(arr) != 3:
        return None
    return Vector3(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))


def _to_bbox_summary(box: Any) -> Optional[BoundingBoxSummary]:
    if box is None:
        return None
    return BoundingBoxSummary(
        min=_to_vector3(box.min_corner) or Vector3(x=0.0, y=0.0, z=0.0),
        max=_to_vector3(box.max_corner) or Vector3(x=0.0, y=0.0, z=0.0),
        width=getattr(box, "width", None),
        depth=getattr(box, "depth", None),
        height=getattr(box, "height", None),
    )


def _to_face_summary(face: Any) -> FaceSummary:
    return FaceSummary(
        id=int(face.id),
        area=float(face.area),
        centroid=_to_vector3(face.centroid) or Vector3(x=0.0, y=0.0, z=0.0),
        normal=_to_vector3(face.normal) or Vector3(x=0.0, y=0.0, z=0.0),
        surface_type=getattr(face.surface_type, "value", str(face.surface_type)),
        radius=float(face.radius) if face.radius is not None else None,
        axis=_to_vector3(face.axis) if face.axis is not None else None,
        origin=_to_vector3(face.origin) if face.origin is not None else None,
    )


def _to_edge_summary(edge: Any) -> EdgeSummary:
    return EdgeSummary(
        id=int(edge.id),
        length=float(edge.length),
        curve_type=getattr(edge.curve_type, "value", str(edge.curve_type)),
        start_point=_to_vector3(edge.start_point) or Vector3(x=0.0, y=0.0, z=0.0),
        end_point=_to_vector3(edge.end_point) or Vector3(x=0.0, y=0.0, z=0.0),
        dihedral_angle=edge.dihedral_angle,
        convex=edge.convex,
    )


def _to_wall_sample_summary(sample: Any) -> WallSampleSummary:
    return WallSampleSummary(
        id=int(sample.id),
        point=_to_vector3(sample.point) or Vector3(x=0.0, y=0.0, z=0.0),
        normal=_to_vector3(sample.normal) or Vector3(x=0.0, y=0.0, z=0.0),
        thickness=float(sample.thickness),
        face_id=int(sample.face_id),
        opposite_face_id=sample.opposite_face_id,
        ray_length=float(sample.ray_length),
        reliable=bool(sample.reliable),
    )


def run_geometry_engine(file_path: str, original_filename: str) -> dict:
    """Run geometry analysis and return a response compatible with GeometryModel."""
    model = load_geometry(file_path)

    response = GeometryEngineResponse(
        status="completed",
        filename=original_filename,
        manufacturability_score=85.0 if model.measurements_reliable else 55.0,
        mock_score=85.0 if model.measurements_reliable else 55.0,
        source_format=getattr(model.source_format, "value", None),
        source_path=model.source_path,
        bounding_box=_to_bbox_summary(model.bounding_box),
        oriented_bbox=_to_bbox_summary(model.oriented_bbox),
        volume_mm3=model.volume_mm3,
        surface_area_mm2=model.surface_area_mm2,
        measurements_reliable=model.measurements_reliable,
        center_mass=_to_vector3(model.center_mass),
        moment_of_inertia=model.moment_of_inertia.tolist()
        if model.moment_of_inertia is not None
        else None,
        faces=[_to_face_summary(face) for face in model.faces],
        edges=[_to_edge_summary(edge) for edge in model.edges],
        wall_samples=[_to_wall_sample_summary(sample) for sample in model.wall_samples],
        nominal_wall=model.nominal_wall,
        face_graph=model.face_graph,
    )

    return response.model_dump()