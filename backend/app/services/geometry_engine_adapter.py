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
import logging
logger = logging.getLogger(__name__)



# Primitive schemas

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



# Topology schemas

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



# Wall thickness schemas

class WallThicknessStatsSummary(BaseModel):
    """Aggregate wall thickness statistics."""
    model_config = ConfigDict(extra="forbid")
    minimum_wall: float
    maximum_wall: float
    mean_wall: float
    median_wall: float
    wall_thickness_field: List[float]



# Mesh quality schema

class MeshQualitySummary(BaseModel):
    """Mesh quality flags (STL path only)."""
    model_config = ConfigDict(extra="forbid")
    is_watertight: bool
    is_winding_consistent: bool
    is_volume: bool



# Print orientation schemas

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



# Cylindrical manufacturing feature schemas (holes / bosses / cavities)

class HoleSummary(BaseModel):
    """A detected cylindrical hole (through, blind, counterbore, countersink)."""
    model_config = ConfigDict(extra="forbid")
    id: int
    type: str
    diameter: float
    depth: float
    axis: Vector3
    center: Vector3
    through: bool
    cylindrical_faces: List[int] = Field(default_factory=list)
    bottom_face: Optional[int] = None
    entry_face: Optional[int] = None
    secondary_diameter: Optional[float] = None
    secondary_depth: Optional[float] = None
    volume_removed: float
    aspect_ratio: float


class BossSummary(BaseModel):
    """A detected cylindrical boss (protrusion)."""
    model_config = ConfigDict(extra="forbid")
    id: int
    outer_diameter: float
    inner_diameter: Optional[float] = None
    wall_thickness: Optional[float] = None
    height: float
    axis: Vector3
    attached_face: Optional[int] = None
    draft_angle: Optional[float] = None
    fillet_radius: Optional[float] = None
    faces: List[int] = Field(default_factory=list)
    is_solid: bool
    height_ratio: float


class CavitySummary(BaseModel):
    """A detected internal cavity / pocket (non-cylindrical recess)."""
    model_config = ConfigDict(extra="forbid")
    id: int
    volume: float
    depth: float
    opening_face: Optional[int] = None
    bottom_faces: List[int] = Field(default_factory=list)
    wall_faces: List[int] = Field(default_factory=list)
    opening_area: float


class FilletSummary(BaseModel):
    """A detected convex rounded-edge blend feature."""
    model_config = ConfigDict(extra="forbid")
    id: int
    radius: float
    length: float
    axis: Vector3
    center: Vector3
    cylindrical_face: int
    adjacent_faces: List[int] = Field(default_factory=list)
    convex: bool
    edge_faces: List[int] = Field(default_factory=list)
    aspect_ratio: float


class RibSummary(BaseModel):
    """A detected thin, long-and-narrow support wall feature."""
    model_config = ConfigDict(extra="forbid")
    id: int
    thickness: float
    length: float
    normal: Vector3
    center: Vector3
    face_pair: List[int] = Field(default_factory=list)
    shared_neighbor_faces: List[int] = Field(default_factory=list)
    aspect_ratio: float


class ChamferSummary(BaseModel):
    """A detected flat (or conical) beveled-edge feature."""
    model_config = ConfigDict(extra="forbid")
    id: int
    width: float
    angle: float
    face: int
    is_conical: bool
    convex: bool
    adjacent_faces: List[int] = Field(default_factory=list)
    valid_edge_count: int
    valid_area_count: int
    is_symmetric_45: bool



# DFM issue schemas

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



# Top-level response schema

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

    # Cylindrical manufacturing features
    holes: List[HoleSummary] = Field(default_factory=list)
    bosses: List[BossSummary] = Field(default_factory=list)
    cavities: List[CavitySummary] = Field(default_factory=list)

    # Blend / bevel manufacturing features
    fillets: List[FilletSummary] = Field(default_factory=list)
    ribs: List[RibSummary] = Field(default_factory=list)
    chamfers: List[ChamferSummary] = Field(default_factory=list)

    # DFM issues
    issues: List[GeometryEngineIssue] = Field(default_factory=list)



# Mapping helpers

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


def _to_hole_summary(hole: Any) -> HoleSummary:
    return HoleSummary(
        id=int(hole.id),
        type=hole.type,
        diameter=float(hole.diameter),
        depth=float(hole.depth),
        axis=_to_vector3(hole.axis) or Vector3(x=0.0, y=0.0, z=0.0),
        center=_to_vector3(hole.center) or Vector3(x=0.0, y=0.0, z=0.0),
        through=bool(hole.through),
        cylindrical_faces=[int(f) for f in hole.cylindrical_faces],
        bottom_face=hole.bottom_face,
        entry_face=hole.entry_face,
        secondary_diameter=hole.secondary_diameter,
        secondary_depth=hole.secondary_depth,
        volume_removed=float(hole.volume_removed()),
        aspect_ratio=float(hole.aspect_ratio()),
    )


def _to_boss_summary(boss: Any) -> BossSummary:
    return BossSummary(
        id=int(boss.id),
        outer_diameter=float(boss.outer_diameter),
        inner_diameter=boss.inner_diameter,
        wall_thickness=boss.wall_thickness,
        height=float(boss.height),
        axis=_to_vector3(boss.axis) or Vector3(x=0.0, y=0.0, z=0.0),
        attached_face=boss.attached_face,
        draft_angle=boss.draft_angle,
        fillet_radius=boss.fillet_radius,
        faces=[int(f) for f in boss.faces],
        is_solid=bool(boss.is_solid()),
        height_ratio=float(boss.height_ratio()),
    )


def _to_cavity_summary(cavity: Any) -> CavitySummary:
    return CavitySummary(
        id=int(cavity.id),
        volume=float(cavity.volume),
        depth=float(cavity.depth),
        opening_face=cavity.opening_face,
        bottom_faces=[int(f) for f in cavity.bottom_faces],
        wall_faces=[int(f) for f in cavity.wall_faces],
        opening_area=float(cavity.opening_area()),
    )


def _to_fillet_summary(fillet: Any) -> FilletSummary:
    return FilletSummary(
        id=int(fillet.id),
        radius=float(fillet.radius),
        length=float(fillet.length),
        axis=_to_vector3(fillet.axis) or Vector3(x=0.0, y=0.0, z=0.0),
        center=_to_vector3(fillet.center) or Vector3(x=0.0, y=0.0, z=0.0),
        cylindrical_face=int(fillet.cylindrical_face),
        adjacent_faces=[int(f) for f in fillet.adjacent_faces],
        convex=bool(fillet.convex),
        edge_faces=[int(f) for f in fillet.edge_faces],
        aspect_ratio=float(fillet.aspect_ratio()),
    )


def _to_rib_summary(rib: Any) -> RibSummary:
    return RibSummary(
        id=int(rib.id),
        thickness=float(rib.thickness),
        length=float(rib.length),
        normal=_to_vector3(rib.normal) or Vector3(x=0.0, y=0.0, z=0.0),
        center=_to_vector3(rib.center) or Vector3(x=0.0, y=0.0, z=0.0),
        face_pair=[int(f) for f in rib.face_pair],
        shared_neighbor_faces=[int(f) for f in rib.shared_neighbor_faces],
        aspect_ratio=float(rib.aspect_ratio()),
    )


def _to_chamfer_summary(chamfer: Any) -> ChamferSummary:
    return ChamferSummary(
        id=int(chamfer.id),
        width=float(chamfer.width),
        angle=float(chamfer.angle),
        face=int(chamfer.face),
        is_conical=bool(chamfer.is_conical),
        convex=bool(chamfer.convex),
        adjacent_faces=[int(f) for f in chamfer.adjacent_faces],
        valid_edge_count=int(chamfer.valid_edge_count),
        valid_area_count=int(chamfer.valid_area_count),
        is_symmetric_45=bool(chamfer.is_symmetric_45()),
    )


def _clamp_volume(volume: float | None, measurements_reliable: bool) -> float | None:
    """
    Here the physically impossible negative volumes are made None.

    A negative volume indicates the mesh has inverted normals or is
    non-watertight (trimesh computes a signed volume). When
    measurements_reliable is already False the caller knows the
    measurements are suspect; returning None instead of a raw negative
    prevents downstream consumers (score calculation, UI display) from
    receiving a physically impossible value.
    """
    if volume is None:
        return None
    if volume < 0:
        logger.warning(
            "Negative volume detected (%.4f mm³) - mesh may have inverted normals "
            "or be non-watertight. Clamping to None.",
            volume,
        )
        return None
    return volume



# Public entry point

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
        volume_mm3=_clamp_volume(model.volume_mm3, model.measurements_reliable),
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
        # Cylindrical manufacturing features
        holes=[_to_hole_summary(h) for h in model.holes],
        bosses=[_to_boss_summary(b) for b in model.bosses],
        cavities=[_to_cavity_summary(c) for c in model.cavities],
        # Blend / bevel manufacturing features
        fillets=[_to_fillet_summary(f) for f in model.fillets],
        ribs=[_to_rib_summary(r) for r in model.ribs],
        chamfers=[_to_chamfer_summary(c) for c in model.chamfers],
    )

    return response.model_dump()