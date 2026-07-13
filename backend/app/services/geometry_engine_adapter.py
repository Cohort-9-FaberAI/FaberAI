"""Adapter layer between the async worker and the future geometry engine.

Defines the response contract (strict Pydantic schemas) that the Data
Science team's geometry engine must satisfy, and hosts the current mock
implementation until the real engine is delivered. The worker should only
ever call `run_geometry_engine`, so swapping the mock for the real engine
requires no changes outside this module.
"""

import time
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Contract schemas for the future geometry engine response ---

class Vector3(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    z: float


class ThreeJSHighlight(BaseModel):
    """Bounding box coordinates for highlighting a region on the 3D canvas."""
    model_config = ConfigDict(extra="forbid")

    type: str = "bounding_box"
    color: str
    min: Vector3
    max: Vector3
    center: Vector3


class GeometryEngineIssue(BaseModel):
    """A single manufacturability issue reported by the geometry engine."""
    model_config = ConfigDict(extra="forbid")

    type: str
    severity: Literal["high", "medium", "low"]
    message: str
    recommendation: str
    three_js_highlight: ThreeJSHighlight


class GeometryEngineResponse(BaseModel):
    """Expected response from the Data Science geometry engine.

    Validates the engine's output once it is integrated: the mock below
    will be replaced by a call to the real engine whose result is parsed
    with `GeometryEngineResponse.model_validate(...)` before being
    returned to the worker.
    """
    model_config = ConfigDict(extra="forbid")

    manufacturability_score: float = Field(ge=0, le=100)
    issues: List[GeometryEngineIssue] = []


# --- Mock implementation (placeholder until the DS team integrates) ---

def run_geometry_engine(file_path: str, original_filename: str) -> dict:
    """Runs geometry analysis on the given CAD file and returns the result.

    Currently a mock that simulates processing time and returns a
    hardcoded score. Once the real engine lands, this function will invoke
    it with `file_path` and validate its output against
    `GeometryEngineResponse`, keeping the worker unchanged.
    """
    # TODO: When the mock below is replaced by the real Data Science geometry
    # engine, validate its raw output here with
    # GeometryEngineResponse.model_validate(...) before returning to the worker.
    time.sleep(5)
    mock_score = 85

    return {
        "status": "completed",
        "file": original_filename,
        "mock_score": mock_score,
    }
