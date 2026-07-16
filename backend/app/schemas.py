from pydantic import BaseModel, Field
from typing import Any, List, Optional
from enum import Enum
import uuid

# --- Enums ---
class AnalysisStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class IssueSeverity(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

# --- Sub-models ---

class Vector3(BaseModel):
    x: float
    y: float
    z: float

class BoundingBox(BaseModel):
    min: Vector3
    max: Vector3

class ThreeJSHighlight(BaseModel):
    type: str = "bounding_box"
    color: str
    min: Vector3
    max: Vector3
    center: Vector3

class PartMetadata(BaseModel):
    units: str = "mm"
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None

class Issue(BaseModel):
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    severity: IssueSeverity
    message: str
    recommendation: str
    three_js_highlight: ThreeJSHighlight


# --- Main Analysis Schema ---
class AnalysisResult(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    status: AnalysisStatus = AnalysisStatus.pending
    manufacturability_score: Optional[float] = None
    summary: Optional[str] = None
    part_metadata: Optional[PartMetadata] = None
    issues: List[Issue] = []
    # Raw geometry engine output — passed through as-is, no nested validation.
    # Carries the full GeometryEngineResponse payload (bounding_box, volume_mm3,
    # faces, edges, wall_samples, etc.) so nothing gets silently stripped.
    geometry_data: Optional[Any] = None


# --- Database Insert Schema ---
# Flattened version for Supabase row insertion
class AnalysisDBRecord(BaseModel):
    analysis_id: str
    filename: str
    status: str
    manufacturability_score: Optional[float] = None
    results_json: Optional[dict] = None