"""Adapter layer between the async worker and the geometry engine.

This module defines a response contract that mirrors the geometry data
produced by the geometry package and can be consumed by the Celery worker.
The worker should only ever call `run_geometry_engine`, so the backend can
keep working even if the real geometry engine is swapped later.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from geometry.loaders import load_geometry


# ---------------------------------------------------------------------------
# Primitive schemas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Topology schemas
# ---------------------------------------------------------------------------

class FaceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    area: float
    centroid: Vector3
    normal: Vector3
    surface_type: str
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


# ---------------------------------------------------------------------------
# Wall thickness schemas
# ---------------------------------------------------------------------------

class WallThicknessStatsSummary(BaseModel):
    """Aggregate wall thickness statistics."""
    model_config = ConfigDict(extra="forbid")
    minimum_wall: float
    maximum_wall: float
    mean_wall: float
    median_wall: float
    wall_thickness_field: List[float]


# ---------------------------------------------------------------------------
# Mesh quality schema
# ---------------------------------------------------------------------------

class MeshQualitySummary(BaseModel):
    """Mesh quality flags (STL path only)."""
    model_config = ConfigDict(extra="forbid")
    is_watertight: bool
    is_winding_consistent: bool
    is_volume: bool


# ---------------------------------------------------------------------------
# Print orientation schemas
# ---------------------------------------------------------------------------

class PrintOrientationSummary(BaseModel):
    """Analysis result for a single candidate build direction."""
    model_config = ConfigDict(extra="forbid")
    axis_label: str
    axis: List[float]
    min_angle: float
    max_angle: float
    mean_angle: float
    median_angle: float
    face_angles: Dict[int, float]
    overhang_area_mm2: float
    overhang_ratio: float


class PrintOrientationAnalysisSummary(BaseModel):
    """Results for all 6 candidate build orientations."""
    model_config = ConfigDict(extra="forbid")
    orientations: List[PrintOrientationSummary] = Field(default_factory=list)
    recommended: str = ""


# ---------------------------------------------------------------------------
# DFM issue schemas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Top-level response schema
# ---------------------------------------------------------------------------

class GeometryEngineResponse(BaseModel):
    """Full response shape produced by run_geometry_engine()."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "failed"] = "completed"
    filename: str
    manufacturability_score: Optional[float] = Field(default=None, ge=0, le=100)
    mock_score: Optional[float] = Field(default=None, ge=0, le=100)

    # Source info
    source_format: Optional[str] = None
    source_path: Optional[str] = None

    # Core measurements
    bounding_box: Optional[BoundingBoxSummary] = None
    oriented_bbox: Optional[BoundingBoxSummary] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    measurements_reliable: bool = True
    center_mass: Optional[Vector3] = None
    moment_of_inertia: Optional[List[List[float]]] = None

    # Topology
    faces: List[FaceSummary] = Field(default_factory=list)
    edges: List[EdgeSummary] = Field(default_factory=list)
    face_graph: Optional[Dict[int, List[int]]] = None

    # Wall thickness
    wall_samples: List[WallSampleSummary] = Field(default_factory=list)
    nominal_wall: Optional[float] = None
    wall_thickness_stats: Optional[WallThicknessStatsSummary] = None

    # Mesh quality (STL only)
    mesh_quality: Optional[MeshQualitySummary] = None

    # Print orientation analysis
    print_orientations: Optional[PrintOrientationAnalysisSummary] = None

    # DFM issues
    issues: List[GeometryEngineIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

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


def _to_wall_thickness_stats(stats: Any) -> Optional[WallThicknessStatsSummary]:
    if stats is None:
        return None
    return WallThicknessStatsSummary(
        minimum_wall=float(stats.minimum_wall),
        maximum_wall=float(stats.maximum_wall),
        mean_wall=float(stats.mean_wall),
        median_wall=float(stats.median_wall),
        wall_thickness_field=[float(t) for t in stats.wall_thickness_field],
    )


def _to_mesh_quality(mq: Any) -> Optional[MeshQualitySummary]:
    if mq is None:
        return None
    return MeshQualitySummary(
        is_watertight=bool(mq.is_watertight),
        is_winding_consistent=bool(mq.is_winding_consistent),
        is_volume=bool(mq.is_volume),
    )


def _to_print_orientation_analysis(analysis: Any) -> Optional[PrintOrientationAnalysisSummary]:
    if analysis is None:
        return None
    orientations = [
        PrintOrientationSummary(
            axis_label=o.axis_label,
            axis=[float(v) for v in o.axis],
            min_angle=float(o.min_angle),
            max_angle=float(o.max_angle),
            mean_angle=float(o.mean_angle),
            median_angle=float(o.median_angle),
            face_angles={int(k): float(v) for k, v in o.face_angles.items()},
            overhang_area_mm2=float(o.overhang_area_mm2),
            overhang_ratio=float(o.overhang_ratio),
        )
        for o in analysis.orientations
    ]
    return PrintOrientationAnalysisSummary(
        orientations=orientations,
        recommended=analysis.recommended,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_geometry_engine(file_path: str, original_filename: str) -> dict:
    """Run geometry analysis and return a fully-populated response dict."""
    model = load_geometry(file_path)

    response = GeometryEngineResponse(
        status="completed",
        filename=original_filename,
        manufacturability_score=85.0 if model.measurements_reliable else 55.0,
        mock_score=85.0 if model.measurements_reliable else 55.0,
        source_format=getattr(model.source_format, "value", None),
        source_path=model.source_path,
        # Core measurements
        bounding_box=_to_bbox_summary(model.bounding_box),
        oriented_bbox=_to_bbox_summary(model.oriented_bbox),
        volume_mm3=model.volume_mm3,
        surface_area_mm2=model.surface_area_mm2,
        measurements_reliable=model.measurements_reliable,
        center_mass=_to_vector3(model.center_mass),
        moment_of_inertia=(
            model.moment_of_inertia.tolist()
            if model.moment_of_inertia is not None
            else None
        ),
        # Topology
        faces=[_to_face_summary(f) for f in model.faces],
        edges=[_to_edge_summary(e) for e in model.edges],
        face_graph=model.face_graph,
        # Wall thickness
        wall_samples=[_to_wall_sample_summary(s) for s in model.wall_samples],
        nominal_wall=model.nominal_wall,
        wall_thickness_stats=_to_wall_thickness_stats(model.wall_thickness_stats),
        # Mesh quality (STL only)
        mesh_quality=_to_mesh_quality(model.mesh_quality),
        # Print orientations
        print_orientations=_to_print_orientation_analysis(model.print_orientations),
    )

    return response.model_dump()
