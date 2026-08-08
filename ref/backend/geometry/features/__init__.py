"""Public API for geometry.features — import from here, not the submodules."""

from .holes import detect_holes, detect_cylindrical_holes, classify_hole, measure_hole
from .bosses import detect_bosses, detect_bosses_full, measure_boss, find_attached_face
from .cavities import detect_cavities, detect_cavities_full, measure_cavity

__all__ = [
    "detect_holes",
    "detect_cylindrical_holes",
    "classify_hole",
    "measure_hole",
    "detect_bosses",
    "detect_bosses_full",
    "measure_boss",
    "find_attached_face",
    "detect_cavities",
    "detect_cavities_full",
    "measure_cavity",
]