"""Injection molding check-set (M1–M7).

Adding a rule: create the module, then list the class in ``INJECTION_MOLDING_RULES``
and give it a threshold block in ``dfm/config/thresholds.yaml``. Nothing else in
the engine needs to change.
"""

from .m1_wall_thickness import WallThicknessRule
from .m2_wall_uniformity import WallUniformityRule
from .m3_draft_angle import DraftAngleRule
from .m4_undercuts import UndercutRule
from .m5_rib_ratio import RibThicknessRule
from .m6_boss_design import BossDesignRule
from .m7_tolerance import ToleranceFeasibilityRule

INJECTION_MOLDING_RULES = [
    WallThicknessRule,
    WallUniformityRule,
    DraftAngleRule,
    UndercutRule,
    RibThicknessRule,
    BossDesignRule,
    ToleranceFeasibilityRule,
]

__all__ = [
    "INJECTION_MOLDING_RULES",
    "WallThicknessRule",
    "WallUniformityRule",
    "DraftAngleRule",
    "UndercutRule",
    "RibThicknessRule",
    "BossDesignRule",
    "ToleranceFeasibilityRule",
]
