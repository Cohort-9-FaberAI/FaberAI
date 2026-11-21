"""Exercise the credential-free setup with real CAD, persistence, and PDFs."""

import io
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
import trimesh
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount

import main
from app import crud, database, local_store
from app.schemas import AnalysisResult
from app.services import pdf_mesh_renderer, storage
from core import workers


@pytest.fixture
def local_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("FABERAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FABERAI_PUBLIC_API_URL", "http://127.0.0.1:8000")
    for module in (database, crud, storage, main):
        monkeypatch.setattr(module, "LOCAL_MODE", True)
    monkeypatch.setattr(
        main.app.router,
        "routes",
        [*main.app.router.routes, Mount("/files", StaticFiles(directory=local_store.files_dir()))],
    )

    def no_network(*args, **kwargs):
        pytest.fail("Local CAD files must not be fetched over HTTP.")

    monkeypatch.setattr(workers.requests, "get", no_network)


def test_local_startup_without_cloud_credentials(tmp_path):
    environment = {
        **os.environ,
        "FABERAI_STORAGE_BACKEND": "local",
        "FABERAI_DATA_DIR": str(tmp_path),
        "SUPABASE_URL": "",
        "SUPABASE_KEY": "",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import main; from app.database import supabase; assert supabase is None"],
        env=environment,
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_local_records_survive_separate_process(local_storage):
    result = AnalysisResult(filename="box.stl")
    crud.insert_analysis_result(result)
    code = (
        "from app.local_store import update_record; "
        f"update_record({result.analysis_id!r}, {{'status': 'completed'}})"
    )
    subprocess.run(
        [sys.executable, "-c", code], cwd=str(Path(__file__).resolve().parents[1]),
        check=True, timeout=30,
    )
    assert crud.get_analysis_by_id(result.analysis_id)["status"] == "completed"


def test_concurrent_local_updates_preserve_fields(local_storage):
    local_store.insert_record({"analysis_id": "shared", "status": "pending"})
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(
            lambda i: local_store.update_record("shared", {f"field_{i}": i}), range(12)
        ))
    record = local_store.get_record("shared")
    assert all(record[f"field_{i}"] == i for i in range(12))


@pytest.mark.parametrize("path", ["../analyses.sqlite3", "/outside.stl", "uploads/../../outside.stl"])
def test_local_files_reject_path_traversal(local_storage, path):
    with pytest.raises(ValueError):
        local_store.save_file(path, b"CAD")


@pytest.mark.parametrize("url", [
    "http://other-host/files/uploads/box.stl",
    "http://127.0.0.1:8000/files/%2e%2e/analyses.sqlite3",
    "http://127.0.0.1:8000/files/..%5canalyses.sqlite3",
    "http://127.0.0.1:8000/analyses.sqlite3",
])
def test_local_file_urls_cannot_read_other_data(local_storage, url):
    with pytest.raises(ValueError):
        local_store.read_file_url(url)


@pytest.mark.parametrize("extension", ["stl", "step"])
def test_upload_analysis_preview_and_report(local_storage, client, monkeypatch, tmp_path, extension):
    if extension == "stl":
        content = trimesh.creation.box(extents=[10, 10, 10]).export(file_type="stl")
    else:
        build123d = pytest.importorskip("build123d")
        step = tmp_path / "box.step"
        build123d.export_step(build123d.Box(10, 10, 10), str(step))
        content = step.read_bytes()

    # Replace only queue transport. Run the real worker, geometry, DFM rules,
    # preview generation, and database updates without a running Redis server.
    def execute(file_url, filename, analysis_id, inputs, tolerance):
        workers.extract_geometry_task.run(file_url, filename, analysis_id, inputs, tolerance)
        return SimpleNamespace(id="local-test-task")

    monkeypatch.setattr(main.extract_geometry_task, "delay", execute)
    monkeypatch.setattr(main, "AsyncResult", lambda *a, **k: SimpleNamespace(state="SUCCESS"))

    uploaded = client.post(
        "/upload/", files={"file": (f"box.{extension}", io.BytesIO(content))},
        data={"material": "abs", "printing_process": "fdm", "tolerance": "standard"},
    )
    assert uploaded.status_code == 202, uploaded.text
    payload = uploaded.json()
    source = client.get(payload["source_file_url"])
    assert source.status_code == 200
    assert source.content == content

    polled = client.get(f"/tasks/{payload['task_id']}", params={"analysis_id": payload["analysis_id"]})
    assert polled.status_code == 200, polled.text
    analysis = polled.json()["result"]
    assert analysis["status"] == "completed"
    assert analysis["dfm_report"]["processes"]
    assert analysis["geometry_data"]["volume_mm3"] == pytest.approx(1000, rel=0.01)
    preview = client.get(analysis["file_url"])
    assert preview.status_code == 200
    mesh = pdf_mesh_renderer._load_mesh_from_source(analysis["file_url"])
    assert mesh is not None and len(mesh.faces) > 0

    pdf = client.post("/analysis/report.pdf", json={"analysis": analysis, "inline": True})
    assert pdf.status_code == 200, pdf.text[:500]
    assert pdf.content.startswith(b"%PDF-")
    assert pdf.headers["content-disposition"].startswith("inline")
    assert client.get(f"/analysis/{payload['analysis_id']}/dfm").status_code == 200

    answer = client.post("/ai/ask", json={"analysis_id": payload["analysis_id"], "question": "What should I fix?"})
    assert answer.status_code == 200, answer.text
    assert answer.json()["mode"] == "deterministic"
