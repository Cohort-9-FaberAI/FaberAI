"""Evaluation context shared by every rule in a single DFM run.

The context is the only place that resolves optional user input against the
YAML defaults, and the only place that reshapes geometry output into the views
several rules need (per-face wall thickness, adjacent-wall pairs, the chosen
build orientation).

It does **no geometry analysis**: every value it exposes is either copied from
the geometry engine payload, aggregated from it (median of samples), or a datum
conversion of an angle the geometry engine already measured. Anything that
would require the CAD kernel belongs upstream.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import DFMConfig, MaterialSpec, PrintingProcessSpec
from .geometry_contract import (
    FaceIn,
    GeometryInput,
    PrintOrientationIn,
    WallSampleIn,
)
from .inputs import DFMInputs

# Axis labels used by the geometry engine's orientation analysis.
AXIS_VECTORS: Dict[str, Tuple[float, float, float]] = {
    "+X": (1.0, 0.0, 0.0),
    "-X": (-1.0, 0.0, 0.0),
    "+Y": (0.0, 1.0, 0.0),
    "-Y": (0.0, -1.0, 0.0),
    "+Z": (0.0, 0.0, 1.0),
    "-Z": (0.0, 0.0, -1.0),
}

# Index into a [width, depth, height] extents list for each axis label.
AXIS_EXTENT_INDEX: Dict[str, int] = {
    "+X": 0, "-X": 0, "+Y": 1, "-Y": 1, "+Z": 2, "-Z": 2,
}


def normalise_axis_label(label: Optional[str]) -> Optional[str]:
    """Accept '+z', 'z', 'Z+', '-Z' and return a canonical '+Z' / '-Z'."""
    if not label:
        return None
    text = str(label).strip().upper().replace(" ", "")
    if text in AXIS_VECTORS:
        return text
    if len(text) == 1 and f"+{text}" in AXIS_VECTORS:
        return f"+{text}"
    if len(text) == 2 and text[1] in "+-" and f"{text[1]}{text[0]}" in AXIS_VECTORS:
        return f"{text[1]}{text[0]}"
    return None


@dataclass
class ResolvedValue:
    """A user input after default resolution, with provenance attached.

    ``assumption`` is non-empty only when the value came from a default; rules
    copy it into their ``assumptions`` list so the report always states what it
    assumed, per the spec's degradation rule.
    """

    value: object
    from_user: bool
    assumption: str = ""


@dataclass
class EvaluationContext:
    """Everything a rule needs for one part, one run."""

    geometry: GeometryInput
    inputs: DFMInputs
    config: DFMConfig

    # Populated in __post_init__
    material: Optional[MaterialSpec] = None
    material_assumption: str = ""
    printing_process: PrintingProcessSpec = None  # type: ignore[assignment]
    printing_process_assumption: str = ""
    surface_finish: str = ""
    surface_finish_assumption: str = ""
    parting_axis: str = "+Z"
    parting_axis_assumption: str = ""
    build_axis: Optional[str] = None
    build_axis_assumption: str = ""
    build_envelope_mm: Optional[List[float]] = None
    build_envelope_assumption: str = ""

    _face_index: Dict[int, FaceIn] = field(default_factory=dict, repr=False)
    _thickness_by_face: Optional[Dict[int, float]] = field(default=None, repr=False)
    _adjacent_pairs: Optional[List[Tuple[int, int, float, float]]] = field(
        default=None, repr=False
    )

    # ------------------------------------------------------------------
    # Resolution of optional inputs
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        defaults = self.config.defaults
        self._face_index = {f.id: f for f in self.geometry.faces}

        # Material (Type 1 lookups for M1/M2/M7)
        self.material = self.config.material(self.inputs.material)
        if self.material is None:
            if self.inputs.material:
                self.material_assumption = (
                    f"Material '{self.inputs.material}' is not in the threshold table; "
                    f"generic engineering-thermoplastic limits were used instead."
                )
            else:
                self.material_assumption = (
                    "No material supplied — generic engineering-thermoplastic limits "
                    "were used and confidence lowered accordingly."
                )

        # Printing process (Type 1 lookups for P1/P2/P3/P5)
        resolved_process = self.config.printing_process(self.inputs.printing_process)
        if resolved_process is None:
            resolved_process = self.config.default_printing_process()
            if self.inputs.printing_process:
                self.printing_process_assumption = (
                    f"Printer/process '{self.inputs.printing_process}' is not in the process "
                    f"table; assumed {resolved_process.display_name}."
                )
            else:
                self.printing_process_assumption = (
                    f"No printer/process supplied — assumed {resolved_process.display_name}, "
                    f"the most restrictive common case."
                )
        self.printing_process = resolved_process

        # Surface finish (drives M3)
        finish = (self.inputs.surface_finish or "").strip().lower().replace(" ", "_")
        finish_table = self.config.rule_value("M3", "finish_minimum_deg", {}) or {}
        if finish not in finish_table:
            default_finish = str(defaults.get("surface_finish", "semi_gloss"))
            self.surface_finish_assumption = (
                f"No surface finish supplied — assumed '{default_finish}' "
                f"({finish_table.get(default_finish, 1.0)}° minimum draft per side)."
                if not finish
                else f"Surface finish '{self.inputs.surface_finish}' is unknown — "
                     f"assumed '{default_finish}'."
            )
            finish = default_finish
        self.surface_finish = finish

        # Parting direction (drives M3/M4)
        parting = normalise_axis_label(self.inputs.parting_direction)
        if parting is None:
            parting = normalise_axis_label(defaults.get("parting_direction")) or "+Z"
            self.parting_axis_assumption = (
                f"No parting direction supplied — assumed the mold pulls along {parting}."
            )
        self.parting_axis = parting

        # Build orientation (drives every printing check)
        self.build_axis, self.build_axis_assumption = self._resolve_build_axis()

        # Build envelope (drives P6)
        envelope = self.inputs.build_envelope_mm
        if envelope and len(envelope) == 3 and all(v > 0 for v in envelope):
            self.build_envelope_mm = [float(v) for v in envelope]
        else:
            fallback = defaults.get("build_envelope_mm")
            if fallback and len(fallback) == 3:
                self.build_envelope_mm = [float(v) for v in fallback]
                source = defaults.get("build_envelope_source", "default build envelope")
                self.build_envelope_assumption = (
                    f"No printer envelope supplied — assumed "
                    f"{self.build_envelope_mm[0]:.0f} x {self.build_envelope_mm[1]:.0f} x "
                    f"{self.build_envelope_mm[2]:.0f} mm ({source})."
                )

    def _resolve_build_axis(self) -> Tuple[Optional[str], str]:
        """Pick the build orientation every printing check is measured against.

        Precedence: explicit user choice > the geometry engine's recommended
        (lowest-overhang) orientation > +Z when orientation data is absent.
        """
        forced = normalise_axis_label(self.inputs.build_orientation)
        if forced is not None:
            return forced, ""

        analysis = self.geometry.print_orientations
        if analysis is not None:
            recommended = normalise_axis_label(analysis.recommended)
            if recommended is not None:
                return recommended, (
                    f"Printing checks were measured against the {recommended} build "
                    f"orientation — the lowest-overhang candidate found by the geometry engine."
                )

        return "+Z", (
            "No build orientation analysis available — printing checks assume the part is "
            "built as modelled along +Z."
        )

    # ------------------------------------------------------------------
    # Geometry views
    # ------------------------------------------------------------------

    def face(self, face_id: int) -> Optional[FaceIn]:
        return self._face_index.get(face_id)

    @property
    def total_surface_area(self) -> float:
        if self.geometry.surface_area_mm2:
            return float(self.geometry.surface_area_mm2)
        return float(sum(f.area for f in self.geometry.faces))

    def nominal_wall(self) -> Optional[float]:
        """The part's representative wall thickness — the denominator of every
        ratio in M2/M5/M6. Prefers the geometry engine's own value."""
        if self.geometry.nominal_wall and self.geometry.nominal_wall > 0:
            return float(self.geometry.nominal_wall)
        stats = self.geometry.wall_thickness_stats
        if stats and stats.median_wall and stats.median_wall > 0:
            return float(stats.median_wall)
        field_values = self.geometry.wall_field()
        if field_values:
            return float(statistics.median(field_values))
        return None

    def wall_samples(self) -> List[WallSampleIn]:
        return self.geometry.reliable_wall_samples()

    def thickness_by_face(self) -> Dict[int, float]:
        """Median wall thickness per face, from the sampled thickness field.

        A median (not a mean) so one bad ray cast on a face does not move the
        face's value — the same statistic the geometry engine uses for nominal.
        """
        if self._thickness_by_face is None:
            grouped: Dict[int, List[float]] = {}
            for sample in self.wall_samples():
                if sample.face_id is None:
                    continue
                grouped.setdefault(sample.face_id, []).append(sample.thickness)
            self._thickness_by_face = {
                face_id: float(statistics.median(values))
                for face_id, values in grouped.items()
                if values
            }
        return self._thickness_by_face

    def adjacent_wall_pairs(self) -> List[Tuple[int, int, float, float]]:
        """(face_a, face_b, thickness_a, thickness_b) for every adjacent pair.

        Built from the geometry engine's face graph and its wall samples — the
        local neighbourhood M1's "thin is not judged in isolation" subtlety and
        M2's taper check both need. Returns [] when either input is missing.
        """
        if self._adjacent_pairs is None:
            pairs: List[Tuple[int, int, float, float]] = []
            graph = self.geometry.face_graph or {}
            thickness = self.thickness_by_face()
            seen: set[Tuple[int, int]] = set()
            for raw_face_id, neighbours in graph.items():
                face_id = int(raw_face_id)
                if face_id not in thickness:
                    continue
                for raw_neighbour in neighbours or []:
                    neighbour_id = int(raw_neighbour)
                    if neighbour_id not in thickness:
                        continue
                    key = (min(face_id, neighbour_id), max(face_id, neighbour_id))
                    if key in seen or key[0] == key[1]:
                        continue
                    seen.add(key)
                    pairs.append(
                        (key[0], key[1], thickness[key[0]], thickness[key[1]])
                    )
            self._adjacent_pairs = pairs
        return self._adjacent_pairs

    # ------------------------------------------------------------------
    # Orientation helpers
    # ------------------------------------------------------------------

    def orientation(self, axis_label: Optional[str] = None) -> Optional[PrintOrientationIn]:
        """The geometry engine's per-face angle analysis for one axis."""
        analysis = self.geometry.print_orientations
        if analysis is None:
            return None
        label = normalise_axis_label(axis_label) or self.build_axis
        if label is None:
            return None
        return analysis.by_label(label)

    def build_orientation(self) -> Optional[PrintOrientationIn]:
        return self.orientation(self.build_axis)

    def parting_orientation(self) -> Optional[PrintOrientationIn]:
        """Face angles measured against the mold pull axis (feeds M3/M4)."""
        return self.orientation(self.parting_axis)

    def extents_in_build_frame(self) -> Optional[Tuple[float, float, float]]:
        """(footprint_a, footprint_b, height) for the chosen build axis.

        Reuses the bounding-box extents the geometry engine already produced and
        permutes them so 'height' means "along the build direction". No new
        geometry is computed.
        """
        extents = self.geometry.bbox_extents()
        if extents is None:
            return None
        index = AXIS_EXTENT_INDEX.get(self.build_axis or "+Z", 2)
        height = extents[index]
        footprint = [e for i, e in enumerate(extents) if i != index]
        return float(footprint[0]), float(footprint[1]), float(height)

    def overhang_angle_from_vertical(self, normal_angle_deg: float) -> float:
        """Convert the geometry engine's datum to the spec's datum.

        The geometry engine reports the angle between a face normal and the
        build axis: 0° = the face points along the build direction, 90° = a
        vertical wall, 180° = the face points straight down.

        The spec measures overhang FROM VERTICAL: a vertical wall is 0° and a
        horizontal downward face is 90°. So for down-facing faces
        (normal angle > 90°) the overhang angle is ``normal_angle - 90``.
        Up-facing faces are never overhangs and return 0.
        """
        if normal_angle_deg <= 90.0:
            return 0.0
        return float(normal_angle_deg - 90.0)

    def angle_between_axis_and_vector(
        self, axis_label: str, vector: Tuple[float, float, float]
    ) -> Optional[float]:
        """Angle in degrees between an axis label and an arbitrary unit vector.

        Used only to compare a *feature axis already produced by the geometry
        engine* (e.g. a hole axis) against the pull direction — a dot product on
        two supplied vectors, not a geometry measurement.
        """
        axis = AXIS_VECTORS.get(normalise_axis_label(axis_label) or "")
        if axis is None:
            return None
        magnitude = math.sqrt(sum(component * component for component in vector))
        if magnitude == 0:
            return None
        dot = sum(a * b for a, b in zip(axis, vector)) / magnitude
        return math.degrees(math.acos(max(-1.0, min(1.0, dot))))

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def input_echo(self) -> Dict[str, object]:
        """User inputs plus what the engine resolved them to — copied into the
        report so the AI layer can explain which values a verdict rests on."""
        return {
            "process": self.inputs.process.value if self.inputs.process else None,
            "material": self.inputs.material,
            "material_resolved": self.material.key if self.material else None,
            "material_class": self.material.material_class if self.material else None,
            "surface_finish": self.surface_finish,
            "surface_finish_supplied": bool(self.inputs.surface_finish),
            "parting_direction": self.parting_axis,
            "printing_process": self.printing_process.key,
            "printing_process_supplied": bool(self.inputs.printing_process),
            "printer_name": self.inputs.printer_name,
            "build_envelope_mm": self.build_envelope_mm,
            "build_envelope_supplied": bool(self.inputs.build_envelope_mm),
            "build_orientation": self.build_axis,
            "tolerances_supplied": len(self.inputs.tolerances),
        }


def build_context(
    geometry_payload: object,
    inputs: Optional[DFMInputs],
    config: DFMConfig,
) -> EvaluationContext:
    """Parse a geometry payload and user inputs into an EvaluationContext."""
    geometry = GeometryInput.from_payload(geometry_payload)
    return EvaluationContext(
        geometry=geometry,
        inputs=inputs or DFMInputs(),
        config=config,
    )
