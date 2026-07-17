"""Candidate print orientation analysis.

Evaluates 6 axis-aligned build directions (+X, -X, +Y, -Y, +Z, -Z) and
reports, for each orientation, how much of the part's surface area faces
downward (overhangs) and the distribution of face angles relative to the
build axis.

The overhang threshold is the standard FDM/SLA heuristic: faces whose
normal makes an angle > 90° with the build axis (i.e. they point away
from the build direction) are overhanging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from geometry.models.face import Face
from geometry.measurements.faceangles import compute_face_angles


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

# The six canonical axis-aligned build directions.
CANDIDATE_AXES: dict[str, np.ndarray] = {
    "+X": np.array([1.0, 0.0, 0.0]),
    "-X": np.array([-1.0, 0.0, 0.0]),
    "+Y": np.array([0.0, 1.0, 0.0]),
    "-Y": np.array([0.0, -1.0, 0.0]),
    "+Z": np.array([0.0, 0.0, 1.0]),
    "-Z": np.array([0.0, 0.0, -1.0]),
}

# Faces whose normal-to-axis angle exceeds this threshold are overhangs.
OVERHANG_ANGLE_DEG: float = 90.0


@dataclass
class PrintOrientationResult:
    """Analysis for a single candidate build direction."""

    axis_label: str           # e.g. "+Z"
    axis: list[float]         # unit vector as [x, y, z]

    # Face angle statistics (degrees, relative to the build axis)
    min_angle: float
    max_angle: float
    mean_angle: float
    median_angle: float

    # Per-face angle mapping  {face_id: angle_deg}
    face_angles: dict[int, float]

    # Overhang metrics
    # Total surface area of faces that overhang (angle > OVERHANG_ANGLE_DEG)
    overhang_area_mm2: float
    # Overhang area as a fraction of total surface area [0, 1]
    overhang_ratio: float


@dataclass
class PrintOrientationAnalysis:
    """Results for all 6 candidate build orientations."""

    orientations: list[PrintOrientationResult] = field(default_factory=list)
    # Label of the orientation with the lowest overhang ratio
    recommended: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_print_orientations(
    faces: Iterable[Face],
) -> PrintOrientationAnalysis:
    """Evaluate all 6 axis-aligned build directions for a set of faces.

    Parameters
    ----------
    faces : Iterable[Face]
        Face objects with populated ``normal`` and ``area`` fields.

    Returns
    -------
    PrintOrientationAnalysis
        Results for every candidate axis plus a recommended orientation.
    """
    # Materialise once so we can iterate multiple times
    face_list = list(faces)
    if not face_list:
        return PrintOrientationAnalysis()

    total_area = sum(f.area for f in face_list)
    # Build a fast lookup: face_id -> area
    area_by_id = {f.id: f.area for f in face_list}

    results: list[PrintOrientationResult] = []

    for label, axis in CANDIDATE_AXES.items():
        face_angles = compute_face_angles(face_list, axis)
        if not face_angles:
            continue

        angles = np.array(list(face_angles.values()), dtype=float)
        ids = list(face_angles.keys())

        # Overhang: faces pointing away from the build direction
        overhang_area = sum(
            area_by_id.get(fid, 0.0)
            for fid, ang in face_angles.items()
            if ang > OVERHANG_ANGLE_DEG
        )
        overhang_ratio = overhang_area / total_area if total_area > 0 else 0.0

        results.append(PrintOrientationResult(
            axis_label=label,
            axis=axis.tolist(),
            min_angle=float(angles.min()),
            max_angle=float(angles.max()),
            mean_angle=float(angles.mean()),
            median_angle=float(np.median(angles)),
            face_angles={fid: face_angles[fid] for fid in ids},
            overhang_area_mm2=float(overhang_area),
            overhang_ratio=float(overhang_ratio),
        ))

    # Recommend the orientation with the smallest overhang ratio.
    # Break ties by lowest mean angle (faces more parallel to build direction).
    recommended = ""
    if results:
        best = min(results, key=lambda r: (r.overhang_ratio, r.mean_angle))
        recommended = best.axis_label

    return PrintOrientationAnalysis(orientations=results, recommended=recommended)
