"""Application-level exceptions for geometry.loaders."""

from __future__ import annotations


class StepSupportUnavailableError(RuntimeError):
    """Raised when a STEP/STP file is processed but the optional STEP
    dependencies are not installed.

    STEP support is an optional feature: pythonocc-core is only distributed
    via Conda and build123d is deliberately kept out of requirements.txt, so
    the rest of the application (STL path, API, worker) must keep working
    without them. See the "Optional STEP support" section of the top-level
    README for installation instructions.
    """
