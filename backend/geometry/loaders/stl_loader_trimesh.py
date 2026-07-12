from __future__ import annotations


def load_stl(path: str):
    """Load an STL file into a trimesh.Trimesh."""
    import trimesh

    return trimesh.load(path, force="mesh")