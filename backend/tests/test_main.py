"""
Unit tests for the FastAPI routes in main.py.

The Supabase Storage upload and Celery dispatch in /upload/ are mocked so no
storage bucket or Redis broker is required, and Supabase credentials are faked
in conftest.py so no database is touched.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from app.schemas import AnalysisResult
from app.services import storage
from app.services.storage import validate_upload_filename


class TestHealthCheck:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_ok_payload(self, client):
        body = client.get("/").json()
        assert body == {"status": "ok", "message": "FaberAI backend is running."}

    def test_dependency_health_returns_200_when_queue_is_ready(self, client):
        response = client.get("/health/dependencies")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_dependency_health_returns_500_when_queue_is_down(self, client, monkeypatch):
        def fail():
            raise HTTPException(
                status_code=500,
                detail={
                    "component": "celery_worker",
                    "message": "No analysis worker is online. Restart the Celery worker.",
                },
            )

        monkeypatch.setattr(main, "_check_analysis_queue", fail)

        response = client.get("/health/dependencies")
        assert response.status_code == 500
        error = response.json()["error"]
        assert error["code"] == 500
        assert "No analysis worker is online" in error["message"]
        assert error["details"]["component"] == "celery_worker"


class TestAnalyzeMock:
    def test_analysis_result_schema_exposes_process_scores(self):
        result = AnalysisResult(
            filename="demo.stl",
            manufacturability_score=72.0,
            printing_score=81.0,
            molding_score=55.0,
            printing_manufacturable=True,
            molding_manufacturable=False,
        )

        payload = result.model_dump()

        assert payload["printing_score"] == 81.0
        assert payload["molding_score"] == 55.0
        assert payload["printing_manufacturable"] is True
        assert payload["molding_manufacturable"] is False

    def test_returns_200(self, client):
        response = client.post("/analyze-mock")
        assert response.status_code == 200

    def test_matches_agreed_api_contract(self, client):
        body = client.post("/analyze-mock").json()

        assert body["analysis_id"] == "mock-analysis-0001"
        assert body["status"] == "completed"
        assert isinstance(body["manufacturability_score"], int)
        assert "part_metadata" in body
        assert "bounding_box" in body["part_metadata"]

    def test_mock_issues_format(self, client):
        body = client.post("/analyze-mock").json()

        assert len(body["issues"]) == 3
        for issue in body["issues"]:
            assert "severity" in issue
            assert "centroid" in issue
            assert len(issue["centroid"]) == 3
            assert "face_id" in issue or "edge_id" in issue


class TestUpload:
    def _upload(self, client, filename="bracket.stl"):
        return client.post(
            "/upload/",
            files={"file": (filename, b"solid mock-geometry", "application/octet-stream")},
        )

    # What upload_cad_file_to_storage returns for bracket.stl; mocked so the
    # tests never talk to real Supabase Storage.
    STORAGE_RESULT = {
        "storage_path": "uploads/mock-uuid.stl",
        "public_url": "https://test-project.supabase.co/storage/v1/object/public/cad-uploads/uploads/mock-uuid.stl",
        "original_filename": "bracket.stl",
    }

    def test_returns_202_and_dispatches_celery_task(self, client):
        with patch.object(
            main, "upload_cad_file_to_storage", return_value=self.STORAGE_RESULT
        ), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ) as mock_delay:
            response = self._upload(client)

        assert response.status_code == 202
        mock_delay.assert_called_once()

    def test_response_body_contains_task_info(self, client):
        with patch.object(
            main, "upload_cad_file_to_storage", return_value=self.STORAGE_RESULT
        ), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ):
            body = self._upload(client).json()

        assert body["task_id"] == "task-123"
        assert body["filename"] == "bracket.stl"
        assert body["status"] == "pending"
        assert body["file_url"] == self.STORAGE_RESULT["public_url"]
        assert body["source_file_url"] == self.STORAGE_RESULT["public_url"]

    def test_upload_forwards_setup_inputs_to_celery_task(self, client):
        with patch.object(
            main, "upload_cad_file_to_storage", return_value=self.STORAGE_RESULT
        ), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ) as mock_delay:
            response = client.post(
                "/upload/",
                files={"file": ("bracket.stl", b"solid mock-geometry", "application/octet-stream")},
                data={
                    "quantity": "12",
                    "material": "ABS",
                    "tolerance": "tight",
                    "process": "printing",
                    "notes": "Test notes",
                },
            )

        assert response.status_code == 202
        assert mock_delay.call_args.args[3] == {
            "quantity": 12,
            "material": "ABS",
            "tolerance": "tight",
            "process": "printing",
            "notes": "Test notes",
        }

    def test_missing_file_returns_422(self, client):
        response = client.post("/upload/")
        assert response.status_code == 422

    def test_upload_returns_500_when_analysis_queue_is_down(self, client, monkeypatch):
        def fail():
            raise HTTPException(
                status_code=500,
                detail={
                    "component": "celery_worker",
                    "message": "No analysis worker is online. Restart the Celery worker.",
                },
            )

        monkeypatch.setattr(main, "_check_analysis_queue", fail)

        response = self._upload(client)
        assert response.status_code == 500
        error = response.json()["error"]
        assert error["code"] == 500
        assert "No analysis worker is online" in error["message"]
        assert error["details"]["component"] == "celery_worker"


class TestUploadValidation:
    """
    Exercises the real upload_cad_file_to_storage validation through the
    /upload/ route, with only the Supabase client mocked so no storage
    bucket is required. Invalid uploads must fail before Supabase is
    touched or a Celery task is dispatched.
    """

    def _upload(self, client, filename, content=b"solid mock-geometry"):
        return client.post(
            "/upload/",
            files={"file": (filename, content, "application/octet-stream")},
        )

    def test_missing_filename_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_upload_filename(None)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Filename is required."

    def test_empty_filename_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_upload_filename("")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Filename is required."

    def test_filename_without_extension_returns_400(self, client):
        with patch.object(storage, "supabase") as mock_supabase:
            response = self._upload(client, "bracket")

        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == 400
        assert error["message"] == "Filename must include a file extension."
        mock_supabase.storage.from_.assert_not_called()

    def test_unsupported_extension_returns_400_listing_formats(self, client):
        with patch.object(storage, "supabase") as mock_supabase:
            response = self._upload(client, "bracket.exe")

        assert response.status_code == 400
        message = response.json()["error"]["message"]
        assert "Unsupported file extension '.exe'" in message
        for ext in (".step", ".stp", ".stl"):
            assert ext in message
        mock_supabase.storage.from_.assert_not_called()

    def test_upload_over_size_limit_returns_413(self, client, monkeypatch):
        monkeypatch.setattr(storage, "MAX_UPLOAD_SIZE_BYTES", 10)
        with patch.object(storage, "supabase") as mock_supabase:
            response = self._upload(client, "bracket.stl", content=b"x" * 11)

        assert response.status_code == 413
        assert "maximum upload size" in response.json()["error"]["message"]
        mock_supabase.storage.from_.assert_not_called()

    def test_upload_at_size_limit_is_accepted(self, client, monkeypatch):
        monkeypatch.setattr(storage, "MAX_UPLOAD_SIZE_BYTES", 10)
        mock_supabase = MagicMock()
        with patch.object(storage, "supabase", mock_supabase), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-456"),
        ):
            response = self._upload(client, "bracket.stl", content=b"x" * 10)

        assert response.status_code == 202

    def test_supported_upload_succeeds_through_real_storage_function(self, client):
        mock_supabase = MagicMock()
        mock_supabase.storage.from_.return_value.get_public_url.return_value = (
            TestUpload.STORAGE_RESULT["public_url"]
        )
        with patch.object(storage, "supabase", mock_supabase), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-456"),
        ):
            response = self._upload(client, "bracket.stl")

        assert response.status_code == 202
        body = response.json()
        assert body["task_id"] == "task-456"
        assert body["filename"] == "bracket.stl"
        assert body["status"] == "pending"

        # The file content reaches Supabase intact, under a unique .stl path.
        upload_call = mock_supabase.storage.from_.return_value.upload
        upload_call.assert_called_once()
        assert upload_call.call_args.kwargs["file"] == b"solid mock-geometry"
        assert upload_call.call_args.kwargs["path"].startswith("uploads/")
        assert upload_call.call_args.kwargs["path"].endswith(".stl")


class TestGetTaskStatus:
    def _mock_async_result(self, state, result=None, traceback=None):
        return SimpleNamespace(state=state, result=result, traceback=traceback)

    def test_failure_does_not_leak_exception_details(self, client):
        secret = "psycopg2 connect failed: host=internal-db.faber.local /srv/uploads/part.stl"
        with patch.object(
            main,
            "AsyncResult",
            return_value=self._mock_async_result("FAILURE", RuntimeError(secret)),
        ):
            response = client.get("/tasks/task-123")

        assert response.status_code == 200
        assert secret not in response.text
        assert "internal-db" not in response.text

    def test_failure_returns_generic_error_message(self, client):
        with patch.object(
            main,
            "AsyncResult",
            return_value=self._mock_async_result("FAILURE", RuntimeError("boom")),
        ):
            body = client.get("/tasks/task-123").json()

        assert body == {
            "task_id": "task-123",
            "status": "FAILURE",
            "error": "Analysis failed. Please try again later.",
        }

    def test_pending_polling_behavior_unchanged(self, client):
        with patch.object(
            main, "AsyncResult", return_value=self._mock_async_result("PENDING")
        ):
            response = client.get("/tasks/task-123")

        assert response.status_code == 200
        assert response.json() == {"task_id": "task-123", "status": "PENDING"}

    def test_completed_db_record_wins_over_stale_celery_pending(self, client):
        stored_result = {
            "analysis_id": "analysis-123",
            "filename": "bracket.stp",
            "status": "completed",
            "manufacturability_score": 25,
            "file_url": "https://example.test/previews/bracket.stl",
            "source_file_url": "https://example.test/uploads/bracket.stp",
            "geometry_data": {
                "source_format": "step",
                "preview_url": "https://example.test/previews/bracket.stl",
            },
            "dfm_report": {"manufacturability_score": 25, "processes": []},
            "issues": [],
        }
        with patch.object(
            main, "AsyncResult", return_value=self._mock_async_result("PENDING")
        ), patch.object(
            main,
            "get_analysis_by_id",
            return_value={"status": "completed", "results_json": stored_result},
        ):
            response = client.get("/tasks/task-123?analysis_id=analysis-123")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "SUCCESS"
        assert body["result"]["file_url"] == stored_result["file_url"]
        assert body["result"]["geometry_data"]["preview_url"] == stored_result["file_url"]

    def test_completed_step_record_backfills_missing_preview(self, client):
        stored_result = {
            "analysis_id": "analysis-123",
            "filename": "bracket.stp",
            "status": "completed",
            "manufacturability_score": 25,
            "file_url": "https://example.test/uploads/bracket.stp",
            "source_file_url": "https://example.test/uploads/bracket.stp",
            "geometry_data": {"source_format": "step"},
            "dfm_report": {"manufacturability_score": 25, "processes": []},
            "issues": [],
        }
        repaired_result = {
            **stored_result,
            "file_url": "https://example.test/previews/bracket.stl",
            "geometry_data": {
                "source_format": "step",
                "preview_url": "https://example.test/previews/bracket.stl",
            },
        }
        with patch.object(
            main, "AsyncResult", return_value=self._mock_async_result("PENDING")
        ), patch.object(
            main,
            "get_analysis_by_id",
            return_value={"status": "completed", "results_json": stored_result},
        ), patch.object(
            main, "_attach_missing_step_preview", return_value=repaired_result
        ) as mock_repair:
            response = client.get("/tasks/task-123?analysis_id=analysis-123")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "SUCCESS"
        assert body["result"]["file_url"] == repaired_result["file_url"]
        assert body["result"]["geometry_data"]["preview_url"] == repaired_result["file_url"]
        mock_repair.assert_called_once()

    def test_pending_task_returns_500_when_worker_is_down(self, client, monkeypatch):
        def fail():
            raise HTTPException(
                status_code=500,
                detail={
                    "component": "celery_worker",
                    "message": "No analysis worker is online. Restart the Celery worker.",
                },
            )

        monkeypatch.setattr(main, "_check_analysis_queue", fail)

        with patch.object(
            main, "AsyncResult", return_value=self._mock_async_result("PENDING")
        ):
            response = client.get("/tasks/task-123")

        assert response.status_code == 500
        error = response.json()["error"]
        assert "No analysis worker is online" in error["message"]
        assert error["details"]["component"] == "celery_worker"


class TestErrorHandlers:
    def test_422_uses_standard_error_envelope(self, client):
        # Posting /upload/ without a file triggers a request validation error.
        response = client.post("/upload/")

        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == 422
        assert error["type"] == "validation_error"
        assert error["message"] == "Request validation failed."
        assert error["details"]  # pydantic per-field errors are preserved

    def test_http_exception_uses_standard_error_envelope(self, client):
        response = client.get("/route-that-does-not-exist")

        assert response.status_code == 404
        error = response.json()["error"]
        assert error["code"] == 404
        assert error["type"] == "http_error"

    def test_unhandled_exception_returns_standard_500(self):
        client = TestClient(main.app, raise_server_exceptions=False)
        with patch.object(
            main, "upload_cad_file_to_storage", return_value=TestUpload.STORAGE_RESULT
        ), patch.object(
            main, "insert_analysis_result"
        ), patch.object(
            main.extract_geometry_task, "delay", side_effect=RuntimeError("boom")
        ):
            response = client.post(
                "/upload/", files={"file": ("bracket.stl", b"solid mock-geometry")}
            )

        assert response.status_code == 500
        assert response.json() == {
            "error": {
                "code": 500,
                "type": "internal_server_error",
                "message": "An unexpected internal error occurred.",
            }
        }
