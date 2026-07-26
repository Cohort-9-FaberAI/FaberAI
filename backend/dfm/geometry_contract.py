"""The geometry engine → DFM engine contract.

This is a *read-only* view of the payload produced by
``app.services.geometry_engine_adapter.GeometryEngineResponse``. It is redefined
here (rather than imported) for two reasons:

* ``dfm/`` stays a pure package with no dependency on the web layer, matching
  how ``geometry/`` is structured;
* every field is optional and unknown fields are allowed, so a geometry engine
  that grows new outputs never breaks the rule engine — rules ask for what they
  need and degrade to "Not assessed" when it is absent.

Feature arrays the geometry team has not shipped yet (``ribs``, ``bosses`` with
base thickness, ``undercuts``, ``trapped_volumes``, ``support_estimates``) are
declared here with their expected shape. They default to ``None`` — *not* to an
empty list — so the engine can tell "geometry did not run this extractor"
(→ Not assessed) apart from "geometry ran it and found nothing" (→ pass).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Loose(BaseModel):
    """Base for every contract model: tolerant of unknown/extra fields."""

    model_config = ConfigDict(extra="allow")


class Vector3In(_Loose):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_list(self) -> List[float]:
        return [self.x, self.y, self.z]


class BoundingBoxIn(_Loose):
    min: Optional[Vector3In] = None
    max: Optional[Vector3In] = None
    width: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None

    def extents(self) -> Optional[List[float]]:
        """[width, depth, height] in mm, derived from corners when absent."""
        if self.width is not None and self.depth is not None and self.height is not None:
            return [self.width, self.depth, self.height]
        if self.min is not None and self.max is not None:
            return [
                abs(self.max.x - self.min.x),
                abs(self.max.y - self.min.y),
                abs(self.max.z - self.min.z),
            ]
        return None


class FaceIn(_Loose):
    id: int
    area: float = 0.0
    centroid: Optional[Vector3In] = None
    normal: Optional[Vector3In] = None
    surface_type: Optional[str] = None
    radius: Optional[float] = None
    axis: Optional[Vector3In] = None
    origin: Optional[Vector3In] = None


class EdgeIn(_Loose):
    id: int
    length: float = 0.0
    curve_type: Optional[str] = None
    dihedral_angle: Optional[float] = None
    convex: Optional[bool] = None


class WallSampleIn(_Loose):
    id: int
    point: Optional[Vector3In] = None
    normal: Optional[Vector3In] = None
    thickness: float = 0.0
    face_id: Optional[int] = None
    opposite_face_id: Optional[int] = None
    ray_length: Optional[float] = None
    reliable: bool = True


class WallThicknessStatsIn(_Loose):
    minimum_wall: Optional[float] = None
    maximum_wall: Optional[float] = None
    mean_wall: Optional[float] = None
    median_wall: Optional[float] = None
    wall_thickness_field: List[float] = Field(default_factory=list)


class MeshQualityIn(_Loose):
    is_watertight: Optional[bool] = None
    is_winding_consistent: Optional[bool] = None
    is_volume: Optional[bool] = None


class PrintOrientationIn(_Loose):
    """One candidate build direction.

    ``face_angles`` is the angle in degrees between each face normal and the
    build axis: 0° = face points along the build direction (up), 90° = vertical
    wall, 180° = face points straight down. P1/P3 convert this to the spec's
    "angle from vertical" datum; see ``rules/printing/p1_overhang.py``.
    """

    axis_label: str = ""
    axis: List[float] = Field(default_factory=list)
    min_angle: Optional[float] = None
    max_angle: Optional[float] = None
    mean_angle: Optional[float] = None
    median_angle: Optional[float] = None
    face_angles: Dict[int, float] = Field(default_factory=dict)
    overhang_area_mm2: Optional[float] = None
    overhang_ratio: Optional[float] = None
    # Forward-compatible: geometry may later ship a real integrated support
    # volume per orientation. When present P3 uses it instead of its estimate.
    support_volume_mm3: Optional[float] = None
    oriented_bbox: Optional[BoundingBoxIn] = None


class PrintOrientationAnalysisIn(_Loose):
    orientations: List[PrintOrientationIn] = Field(default_factory=list)
    recommended: str = ""

    def by_label(self, label: str) -> Optional[PrintOrientationIn]:
        for orientation in self.orientations:
            if orientation.axis_label == label:
                return orientation
        return None


class HoleIn(_Loose):
    id: int
    type: Optional[str] = None
    diameter: float = 0.0
    depth: float = 0.0
    axis: Optional[Vector3In] = None
    center: Optional[Vector3In] = None
    through: Optional[bool] = None
    cylindrical_faces: List[int] = Field(default_factory=list)


class BossIn(_Loose):
    """Cylindrical standoff. ``wall_thickness`` is the value M6 ratios against
    the nominal wall; it is None for a solid boss, which M6 handles separately
    (core-out recommendation) rather than treating as missing data."""

    id: int
    outer_diameter: float = 0.0
    inner_diameter: Optional[float] = None
    wall_thickness: Optional[float] = None
    height: float = 0.0
    axis: Optional[Vector3In] = None
    center: Optional[Vector3In] = None
    attached_face: Optional[int] = None
    draft_angle: Optional[float] = None
    fillet_radius: Optional[float] = None
    faces: List[int] = Field(default_factory=list)
    is_solid: Optional[bool] = None
    height_ratio: Optional[float] = None
    # Expected once feature recognition lands: thickness of the wall the boss
    # sits on. M6 falls back to the part nominal wall when absent.
    base_wall_thickness: Optional[float] = None


class RibIn(_Loose):
    """Thin protruding support wall. ``thickness`` is the rib base thickness
    M5 ratios against the nominal wall."""

    id: int
    thickness: float = 0.0
    length: float = 0.0
    normal: Optional[Vector3In] = None
    center: Optional[Vector3In] = None
    face_pair: List[int] = Field(default_factory=list)
    shared_neighbor_faces: List[int] = Field(default_factory=list)
    aspect_ratio: Optional[float] = None
    # Expected once feature recognition lands: the wall the rib grows from.
    # M5 falls back to the part nominal wall when absent.
    base_wall_thickness: Optional[float] = None


class CavityIn(_Loose):
    """Internal pocket. An opening area of zero / no opening face is what P5
    reads as an enclosed, undrainable volume."""

    id: int
    volume: float = 0.0
    depth: float = 0.0
    opening_face: Optional[int] = None
    bottom_faces: List[int] = Field(default_factory=list)
    wall_faces: List[int] = Field(default_factory=list)
    opening_area: Optional[float] = None
    # Expected from mesh void analysis: set True when the void is fully
    # enclosed. When present P5 trusts it over the opening_area heuristic.
    is_enclosed: Optional[bool] = None


class UndercutIn(_Loose):
    """NOT YET PRODUCED BY THE GEOMETRY ENGINE.

    Declared so M4 works unchanged the day undercut detection lands. Until then
    M4 falls back to a hole-axis inference and, failing that, Not assessed.
    """

    id: int
    face_ids: List[int] = Field(default_factory=list)
    pull_direction: Optional[List[float]] = None
    # True when a side-action / lifter can release the feature (→ Major),
    # False when the feature cannot be released at all (→ Blocker).
    requires_side_action: Optional[bool] = None
    releasable: Optional[bool] = None
    depth: Optional[float] = None
    center: Optional[Vector3In] = None


class GeometryInput(_Loose):
    """The geometry engine payload as the DFM engine reads it."""

    status: Optional[str] = None
    filename: Optional[str] = None
    source_format: Optional[str] = None
    source_path: Optional[str] = None

    bounding_box: Optional[BoundingBoxIn] = None
    oriented_bbox: Optional[BoundingBoxIn] = None
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    measurements_reliable: bool = True
    center_mass: Optional[Vector3In] = None
    moment_of_inertia: Optional[List[List[float]]] = None

    faces: List[FaceIn] = Field(default_factory=list)
    edges: List[EdgeIn] = Field(default_factory=list)
    face_graph: Optional[Dict[int, List[int]]] = None

    wall_samples: List[WallSampleIn] = Field(default_factory=list)
    nominal_wall: Optional[float] = None
    wall_thickness_stats: Optional[WallThicknessStatsIn] = None

    mesh_quality: Optional[MeshQualityIn] = None
    print_orientations: Optional[PrintOrientationAnalysisIn] = None

    holes: List[HoleIn] = Field(default_factory=list)
    cavities: List[CavityIn] = Field(default_factory=list)

    # --- Pending geometry outputs -----------------------------------------
    # Default None (not []) so "extractor never ran" is distinguishable from
    # "extractor ran and found none". See module docstring.
    ribs: Optional[List[RibIn]] = None
    bosses: Optional[List[BossIn]] = None
    undercuts: Optional[List[UndercutIn]] = None
    trapped_volumes: Optional[List[CavityIn]] = None

    @classmethod
    def from_payload(cls, payload: Any) -> "GeometryInput":
        """Accept a dict, an already-parsed model, or any object exposing
        ``model_dump()`` (e.g. ``GeometryEngineResponse``)."""
        if isinstance(payload, cls):
            return payload
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        if not isinstance(payload, dict):
            raise TypeError(
                f"Geometry payload must be a dict or pydantic model, got {type(payload).__name__}"
            )
        return cls.model_validate(payload)

    # --- Convenience accessors used by several rules ----------------------

    def reliable_wall_samples(self) -> List[WallSampleIn]:
        """Wall samples the geometry engine did not flag as unreliable."""
        return [s for s in self.wall_samples if s.reliable and s.thickness > 0]

    def wall_field(self) -> List[float]:
        """All usable wall thickness values, preferring per-sample data over
        the pre-aggregated field so face ids stay available for highlights."""
        samples = self.reliable_wall_samples()
        if samples:
            return [s.thickness for s in samples]
        if self.wall_thickness_stats is not None:
            return [t for t in self.wall_thickness_stats.wall_thickness_field if t > 0]
        return []

    def bbox_extents(self) -> Optional[List[float]]:
        for box in (self.oriented_bbox, self.bounding_box):
            if box is not None:
                extents = box.extents()
                if extents and all(e > 0 for e in extents):
                    return extents
        return None
