"""STEP loading via OpenCASCADE Python bindings.

The project supports both binding namespaces:
* ``OCC.Core`` from pythonocc-core (Conda)
* ``OCP`` from build123d/cadquery wheels (pip)

The rest of the geometry engine only needs a TopoDS_Shape-like object, so this
loader prefers pythonocc-core when present and falls back to OCP in the current
venv.
"""

from __future__ import annotations

from .exceptions import StepSupportUnavailableError

def load_step(path: str):
    """Load a STEP file into a TopoDS_Shape via OpenCASCADE."""
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
    except (ImportError, ModuleNotFoundError):
        try:
            from OCP.STEPControl import STEPControl_Reader
            from OCP.IFSelect import IFSelect_RetDone
        except (ImportError, ModuleNotFoundError) as ocp_exc:
            raise StepSupportUnavailableError(
                "STEP support is unavailable because neither pythonocc-core "
                "nor OCP/build123d is installed. Install build123d with pip "
                "or create the full environment from backend/environment-ds.yml."
            ) from ocp_exc

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
