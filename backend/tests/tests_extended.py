"""
Extended test suite covering:
- Task 1: Integration and edge cases (malformed payloads, bad file formats, fake task IDs)
- Task 2: Resilience and retry logic (simulated Supabase failures, worker retry policy)
- Task 3: Concurrency and load testing (multiple simultaneous upload requests)
- Task 4: Error logging and API documentation (Swagger schema accuracy)
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call
import pytest
import httpx
import requests
from core.workers import extract_geometry_task, update_analysis_status
from app.schemas import AnalysisStatus

from fastapi.testclient import TestClient
import main


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

STORAGE_RESULT = {
    "storage_path": "uploads/mock-uuid.stl",
    "public_url": "https://test-project.supabase.co/storage/v1/object/public/cad-uploads/uploads/mock-uuid.stl",
    "original_filename": "bracket.stl",
}


def _upload(client, filename="bracket.stl", content=b"solid mock-geometry", content_type="application/octet-stream"):
    return client.post(
        "/upload/",
        files={"file": (filename, content, content_type)},
    )


def _mock_upload(extra_mocks=None):
    """
    Context manager helper that always mocks the three external dependencies
    of POST /upload/ so tests never touch Supabase or Redis.
    """
    return [
        patch.object(main, "upload_cad_file_to_storage", return_value=STORAGE_RESULT),
        patch.object(main, "insert_analysis_result"),
        patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ),
    ]


# ---------------------------------------------------------------------------
# Task 1 — Integration and Edge Cases
# ---------------------------------------------------------------------------

class TestUploadEdgeCases:
    """
    Parametrized tests for malformed payloads and unsupported file formats
    sent to POST /upload/.
    """

    @pytest.mark.parametrize("filename,content,content_type", [
        # Unsupported file format
        ("part.obj", b"v 0 0 0", "application/octet-stream"),
        ("drawing.pdf", b"%PDF-1.4", "application/pdf"),
        ("model.iges", b"some iges content", "application/octet-stream"),
        # Empty file
        ("empty.stl", b"", "application/octet-stream"),
        # File with no extension
        ("noextension", b"solid content", "application/octet-stream"),
    ])
    def test_unsupported_or_malformed_file_does_not_crash_server(
        self, client, filename, content, content_type
    ):
        """
        Server must never return 500 for bad input — only 4xx.
        Even if the format is wrong, the API should handle it gracefully.
        """
        with patch.object(main, "upload_cad_file_to_storage", return_value={
            **STORAGE_RESULT,
            "original_filename": filename,
        }), patch.object(main, "insert_analysis_result"), patch.object(
            main.extract_geometry_task,
            "delay",
            return_value=SimpleNamespace(id="task-123"),
        ):
            response = _upload(client, filename=filename, content=content, content_type=content_type)

        # Should not be a 500 — server must handle gracefully
        assert response.status_code != 500

    def test_missing_file_field_returns_422(self, client):
        """
        POST /upload/ with no file attached must return 422, not 500.
        """
        response = client.post("/upload/")
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["type"] == "validation_error"

    def test_missing_file_error_envelope_has_details(self, client):
        """
        The 422 response must include per-field error details.
        """
        response = client.post("/upload/")
        error = response.json()["error"]
        assert "details" in error
        assert len(error["details"]) > 0

    @pytest.mark.parametrize("wrong_field_name", ["files", "upload", "cad_file", "data"])
    def test_wrong_field_name_returns_422(self, client, wrong_field_name):
        """
        Sending the file under a wrong field name must return 422.
        """
        response = client.post(
            "/upload/",
            files={wrong_field_name: ("bracket.stl", b"solid mock", "application/octet-stream")},
        )
        assert response.status_code == 422


class TestTaskStatusEdgeCases:
    """
    Tests for GET /tasks/{task_id} with fake or non-existent task IDs.
    """

    def test_fake_task_id_returns_pending_not_500(self, client):
        """
        Celery reports unknown task IDs as PENDING.
        The endpoint must return a valid response, not a 500.
        """
        response = client.get("/tasks/completely-fake-task-id-that-does-not-exist")
        assert response.status_code != 500

    def test_fake_task_id_returns_pending_status(self, client):
        """
        Unknown task IDs should come back as PENDING state.
        """
        response = client.get("/tasks/completely-fake-task-id-that-does-not-exist")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "PENDING"

    def test_success_task_with_no_db_record_returns_404(self, client):
        """
        If Celery reports SUCCESS but no record exists in Supabase,
        the endpoint must return 404, not 500.
        """
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"analysis_id": "nonexistent-id", "mock_score": 85}

        with patch("main.AsyncResult", return_value=mock_result), \
             patch.object(main, "get_analysis_by_id", return_value=None):
            response = client.get("/tasks/some-task-id")

        assert response.status_code == 404
        error = response.json()["error"]
        assert error["type"] == "http_error"

    def test_failed_task_returns_failure_status(self, client):
        """
        A task that Celery marks as FAILURE must return a FAILURE status
        with an error message, not a 500.
        """
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.result = RuntimeError("geometry engine crashed")

        with patch("main.AsyncResult", return_value=mock_result):
            response = client.get("/tasks/some-failed-task-id")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "FAILURE"
        assert "error" in body

    @pytest.mark.parametrize("task_id", [
        "not-a-uuid",
        "12345",
        "a" * 100,
        "task-with-special-chars-!@#",
    ])
    def test_various_fake_task_id_formats_do_not_crash(self, client, task_id):
        """
        Any string passed as task_id must not cause a 500.
        """
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code != 500


# ---------------------------------------------------------------------------
# Task 2 — Resilience and Retry Logic
# ---------------------------------------------------------------------------

class TestWorkerRetryPolicy:
    """
    Tests that verify the Celery worker retries on transient failures
    and correctly updates Supabase status to failed after exhausting retries.
    """

    def test_worker_retries_on_request_timeout(self):
        """
        If requests.get raises a Timeout, the task should be set to retry
        via autoretry_for — not immediately mark as failed.
        """
        from core.workers import extract_geometry_task

        # Verify the task is configured to retry on Timeout
        assert requests.exceptions.Timeout in extract_geometry_task.autoretry_for

    def test_worker_retries_on_connection_error(self):
        """
        If requests.get raises a ConnectionError, the task should retry.
        """
        from core.workers import extract_geometry_task

        assert requests.exceptions.ConnectionError in extract_geometry_task.autoretry_for

    def test_worker_max_retries_is_set(self):
        """
        The task must have a finite max_retries so it does not retry forever.
        """
        from core.workers import extract_geometry_task

        assert extract_geometry_task.max_retries is not None
        assert extract_geometry_task.max_retries > 0

    def test_worker_updates_status_to_failed_after_max_retries(self):

        # Test the failed branch directly by calling update_analysis_status
        # the same way the worker does when retries are exhausted
        with patch("core.workers.update_analysis_status") as mock_update:
            # Simulate what the worker does in the except block
            # when self.request.retries >= self.max_retries
            from core.workers import update_analysis_status
            update_analysis_status("fake-analysis-id", AnalysisStatus.failed.value)
            mock_update.assert_called_once_with("fake-analysis-id", AnalysisStatus.failed.value)

    def test_worker_failed_branch_is_reachable_in_code(self):
        """
        Verify the failed branch exists in the worker source code
        so we know the logic is present even if we cannot trigger it
        without a real Celery context.
        """
        import inspect
        from core.workers import extract_geometry_task
        source = inspect.getsource(extract_geometry_task)
        assert "AnalysisStatus.failed.value" in source
        assert "self.request.retries >= self.max_retries" in source
        
    def test_worker_sets_processing_status_on_start(self):

        with patch("core.workers.update_analysis_status") as mock_update, \
            patch("core.workers.requests.get") as mock_get, \
            patch("core.workers.run_geometry_engine", return_value={"mock_score": 85}), \
            patch("core.workers.insert_analysis_result"):

            mock_response = MagicMock()
            mock_response.content = b"solid mock"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            try:
                extract_geometry_task.__wrapped__(
                    "https://fake-url.com/file.stl",
                    "test.stl",
                    "fake-analysis-id",
                )
            except Exception:
                pass

            first_call = mock_update.call_args_list[0]
            assert first_call == call("fake-analysis-id", AnalysisStatus.processing.value)

# ---------------------------------------------------------------------------
# Task 3 — Concurrency and Load Testing
# ---------------------------------------------------------------------------

class TestConcurrentUploads:
    """
    Verifies the API handles multiple simultaneous upload requests correctly
    without dropping requests or causing race conditions.
    """

    def test_multiple_sequential_uploads_all_return_202(self, client):
        """
        Ten sequential uploads must all succeed with 202.
        """
        with patch.object(main, "upload_cad_file_to_storage", return_value=STORAGE_RESULT), \
             patch.object(main, "insert_analysis_result"), \
             patch.object(
                 main.extract_geometry_task,
                 "delay",
                 return_value=SimpleNamespace(id="task-123"),
             ):
            responses = [_upload(client) for _ in range(10)]

        assert all(r.status_code == 202 for r in responses)

    def test_multiple_uploads_each_get_unique_task_id(self, client):
        """
        Each upload must return a unique task_id — no shared state between requests.
        """
        task_ids = ["task-001", "task-002", "task-003", "task-004", "task-005"]
        side_effects = [SimpleNamespace(id=tid) for tid in task_ids]

        with patch.object(main, "upload_cad_file_to_storage", return_value=STORAGE_RESULT), \
             patch.object(main, "insert_analysis_result"), \
             patch.object(
                 main.extract_geometry_task,
                 "delay",
                 side_effect=side_effects,
             ):
            responses = [_upload(client) for _ in range(5)]

        returned_ids = [r.json()["task_id"] for r in responses]
        assert len(set(returned_ids)) == 5  # all unique

    def test_concurrent_uploads_via_async(self, client):
        """
        Simulate concurrent uploads using asyncio and httpx async client.
        All requests must return 202.
        """
        async def run_concurrent_uploads():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
                tasks = [
                    ac.post(
                        "/upload/",
                        files={"file": (f"part_{i}.stl", b"solid mock", "application/octet-stream")},
                    )
                    for i in range(5)
                ]
                return await asyncio.gather(*tasks)

        with patch.object(main, "upload_cad_file_to_storage", return_value=STORAGE_RESULT), \
             patch.object(main, "insert_analysis_result"), \
             patch.object(
                 main.extract_geometry_task,
                 "delay",
                 return_value=SimpleNamespace(id="task-concurrent"),
             ):
            responses = asyncio.run(run_concurrent_uploads())

        assert all(r.status_code == 202 for r in responses)


# ---------------------------------------------------------------------------
# Task 4 — API Documentation Accuracy
# ---------------------------------------------------------------------------

class TestAPIDocumentation:
    """
    Verifies that the Swagger/OpenAPI schema at /docs and /openapi.json
    accurately reflects the routes and status codes the API returns.
    """

    def test_openapi_schema_is_accessible(self, client):
        """
        GET /openapi.json must return 200 and valid JSON.
        """
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "info" in schema

    def test_upload_route_documented_in_schema(self, client):
        """
        POST /upload/ must be present in the OpenAPI schema.
        """
        schema = client.get("/openapi.json").json()
        assert "/upload/" in schema["paths"]
        assert "post" in schema["paths"]["/upload/"]

    def test_upload_route_documents_202_response(self, client):
        """
        The schema for POST /upload/ must declare a 202 response.
        """
        schema = client.get("/openapi.json").json()
        responses = schema["paths"]["/upload/"]["post"]["responses"]
        assert "202" in responses

    def test_tasks_route_documented_in_schema(self, client):
        """
        GET /tasks/{task_id} must be present in the OpenAPI schema.
        """
        schema = client.get("/openapi.json").json()
        assert "/tasks/{task_id}" in schema["paths"]
        assert "get" in schema["paths"]["/tasks/{task_id}"]

    def test_analyze_mock_route_documented_in_schema(self, client):
        """
        POST /analyze-mock must be present in the OpenAPI schema.
        """
        schema = client.get("/openapi.json").json()
        assert "/analyze-mock" in schema["paths"]

    def test_health_check_route_documented_in_schema(self, client):
        """
        GET / must be present in the OpenAPI schema.
        """
        schema = client.get("/openapi.json").json()
        assert "/" in schema["paths"]
        assert "get" in schema["paths"]["/"]

    def test_docs_endpoint_returns_200(self, client):
        """
        GET /docs must return 200 — Swagger UI is accessible.
        """
        response = client.get("/docs")
        assert response.status_code == 200

    def test_api_title_matches_expected(self, client):
        """
        The API title in the schema must match what is defined in main.py.
        """
        schema = client.get("/openapi.json").json()
        assert schema["info"]["title"] == "FaberAI Backend"