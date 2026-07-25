"""3D printing check-set (P1–P6).

Every rule here is orientation-relative: it is evaluated against the build
orientation resolved by ``EvaluationContext``, never the part's as-modelled
pose, and each result states which orientation it assumed.
"""

from .p1_overhang import OverhangAngleRule
from .p2_min_feature import MinimumFeatureSizeRule
from .p3_support_volume import SupportVolumeRule
from .p4_aspect_ratio import AspectRatioRule
from .p5_trapped_volumes import TrappedVolumeRule
from .p6_build_envelope import BuildEnvelopeRule

PRINTING_RULES = [
    OverhangAngleRule,
    MinimumFeatureSizeRule,
    SupportVolumeRule,
    AspectRatioRule,
    TrappedVolumeRule,
    BuildEnvelopeRule,
]

__all__ = [
    "PRINTING_RULES",
    "OverhangAngleRule",
    "MinimumFeatureSizeRule",
    "SupportVolumeRule",
    "AspectRatioRule",
    "TrappedVolumeRule",
    "BuildEnvelopeRule",
]
