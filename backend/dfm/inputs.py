"""Optional user context supplied alongside the CAD file.

Every field here is optional by design. The spec's graceful-degradation rule is
absolute: a blank field must never cost the user points. Each rule either falls
back to a stated default from ``thresholds.yaml`` (and says so in the report) or
reports "Not assessed" and drops out of the roll-up denominator.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import ProcessType


class ToleranceRequest(BaseModel):
    """One dimension the user wants held to a stated tolerance (feeds M7)."""

    model_config = ConfigDict(extra="forbid")

    label: str = "dimension"
    # Nominal size of the toleranced feature — capability is size-dependent.
    feature_size_mm: float = Field(gt=0)
    # Requested tolerance as a +/- value in mm.
    requested_tolerance_mm: float = Field(gt=0)
    face_id: Optional[int] = None


class DFMInputs(BaseModel):
    """User-supplied manufacturing context. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    # Which check-set to run. None -> run every process and recommend one.
    process: Optional[ProcessType] = None

    # Estimated production quantity; surfaced in the report context for
    # downstream rules or cost-sensitive downstream workflows.
    quantity: Optional[int] = None

    # --- Injection molding context ---------------------------------------
    material: Optional[str] = None
    # polished | semi_gloss | light_texture | heavy_texture
    surface_finish: Optional[str] = None
    # Mold pull axis as an axis label, e.g. "+Z".
    parting_direction: Optional[str] = None
    # Deepest cavity in the part, if the user knows it. Drives M3's
    # deep-cavity draft bump, which cannot be read from geometry alone.
    max_cavity_depth_mm: Optional[float] = None
    tolerances: List[ToleranceRequest] = Field(default_factory=list)

    # --- 3D printing context ---------------------------------------------
    # fdm | sla | sls | mjf (aliases resolved through thresholds.yaml)
    printing_process: Optional[str] = None
    printer_name: Optional[str] = None
    # [x, y, z] build envelope in mm.
    build_envelope_mm: Optional[List[float]] = None
    # Force a build orientation instead of the geometry engine's recommendation.
    build_orientation: Optional[str] = None

    def processes_to_evaluate(self) -> List[ProcessType]:
        """The check-sets this run should evaluate."""
        if self.process is not None:
            return [self.process]
        return [ProcessType.injection_molding, ProcessType.printing]
