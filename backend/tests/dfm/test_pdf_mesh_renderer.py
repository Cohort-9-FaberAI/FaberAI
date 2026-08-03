from pathlib import Path
from app.services.pdf_mesh_renderer import generate_mesh_snapshots

def test_generate_mesh_snapshots_from_local_stl_with_markers():
    stl_path = Path(__file__).resolve().parent.parent.parent / "datasets" / "STL" / "box_prism.stl"
    assert stl_path.exists(), f"Expected test STL at {stl_path}"
    
    analysis = {
        "file_url": str(stl_path),
        "issues": [
            {"severity": "high", "centroid": [1.0, 1.0, 1.0], "message": "High test defect"},
            {"severity": "medium", "centroid": [-1.0, 0.5, 0.0], "message": "Medium test defect"},
        ],
    }
    snapshots = generate_mesh_snapshots(analysis)
    assert len(snapshots) == 4
    for snap in snapshots:
        content = snap.read()
        assert content.startswith(b"\x89PNG")
        assert len(content) > 100
