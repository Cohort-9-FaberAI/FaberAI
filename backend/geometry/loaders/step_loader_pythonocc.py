"""
STEP loading via pythonOCC (OpenCASCADE).

pythonocc-core is an optional dependency (Conda-only, not pip-installable),
so it is imported lazily inside load_step() and its absence is reported as
StepSupportUnavailableError instead of a raw ImportError.
"""

from __future__ import annotations

from .exceptions import StepSupportUnavailableError


def load_step(path: str):
    """Load a STEP file into a TopoDS_Shape via pythonOCC's STEPControl_Reader."""
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
    except ImportError as exc:
        raise StepSupportUnavailableError(
            "STEP support is unavailable because the optional dependency "
            "'pythonocc-core' is not installed. It cannot be installed with "
            "pip; use Conda instead: 'conda install -c conda-forge "
            "pythonocc-core' (or create the full environment from "
            "backend/environment-ds.yml). Non-STEP formats such as STL are "
            "unaffected."
        ) from exc

    reader = STEPControl_Reader()
    status = reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ValueError(f"Failed to read STEP file: {path}")

    reader.TransferRoots()
    shape = reader.OneShape()

    # OneShape() can return a null TopoDS_Shape when the STEP file contains
    # no valid geometry (e.g. empty file, corrupted data, or only
    # non-geometric entities).  A null shape would later cause a cryptic
    # SWIG TypeError in brepbndlib.Add / brepgprop.VolumeProperties, so we
    # catch it here with a clear, actionable message.
    if shape.IsNull():
        raise ValueError(
            f"STEP file '{path}' contains no valid geometry. "
            "The file may be empty, corrupted, or contain only "
            "non-geometric entities (no shapes were transferred)."
        )

    return shape
