"""
Legacy STEP loading via build123d.

The dispatcher uses the pythonOCC loader (step_loader_pythonocc.py); this
module is kept for callers that want a build123d Shape instead of a raw
TopoDS_Shape. build123d is an optional dependency, so it is imported lazily
inside load_step() and its absence is reported as StepSupportUnavailableError
instead of a raw ImportError.
"""

from __future__ import annotations

from .exceptions import StepSupportUnavailableError


def load_step(file_path):
    try:
        from build123d import import_step
    except ImportError as exc:
        raise StepSupportUnavailableError(
            "STEP support is unavailable because the optional dependency "
            "'build123d' is not installed. Install it with 'pip install "
            "build123d' (or create the full environment from "
            "backend/environment-ds.yml). Non-STEP formats such as STL are "
            "unaffected."
        ) from exc

    shape = import_step(file_path)
    return shape
