"""Enums for the geometry package."""

from enum import Enum


class SourceFormat(str, Enum):
    STEP = "step"
    STL = "stl"