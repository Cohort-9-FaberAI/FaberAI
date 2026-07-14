"""Enums for the geometry package."""

from enum import Enum


class SourceFormat(str, Enum):
    STEP = "step"
    STL = "stl"

class SurfaceType(str, Enum):
    PLANE = "plane"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    CONE = "cone"
    TORUS = "torus"
    BSPLINE = "bspline"
    UNKNOWN = "unknown"

class CurveType(str, Enum):
    LINE = "line"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    SPLINE = "spline"
    UNKNOWN = "unknown"