"""Public API for geometry.loaders — import from here, not the submodules."""

from .dispatcher import load_geometry, get_file_format
from .step_loader_pythonocc import load_step
from .stl_loader_trimesh import load_stl

__all__ = ["load_geometry", "get_file_format", "load_step", "load_stl"]