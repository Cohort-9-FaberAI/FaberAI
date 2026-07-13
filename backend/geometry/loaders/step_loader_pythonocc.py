"""
STEP loading via pythonOCC (OpenCASCADE).

"""

from __future__ import annotations


def load_step(path: str):
    """Load a STEP file into a TopoDS_Shape via pythonOCC's STEPControl_Reader."""
    from OCC.Core.STEPControl import STEPControl_Reader
    from OCC.Core.IFSelect import IFSelect_RetDone

    reader = STEPControl_Reader()
    status = reader.ReadFile(path)
    if status != IFSelect_RetDone:
        raise ValueError(f"Failed to read STEP file: {path}")

    reader.TransferRoots()
    shape = reader.OneShape()
    return shape