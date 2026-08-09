"""DFM and AI HTTP routes.

Supabase is mocked throughout (credentials are faked in the root conftest), so
no database or storage bucket is touched.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import main
from dfm import DFMInputs, run_dfm_analysis
from dfm.models import ProcessType


@pytest.fixture()
def client():
    # The lifespan handler loads the DFM YAML; entering it here proves the app
    # boots with a valid config.
    with TestClient(main.app) as test_client:
        yield test_client


class TestDFMEvaluateEndpoint:
    def test_returns_a_report(self, client, step_geometry):
        response = client.post("/dfm/evaluate", json={"geometry": step_geometry})
        assert response.status_code == 200
        body = response.json()
        assert len(body["processes"]) == 2
        assert "manufacturability_score" in body

    def test_accepts_optional_user_inputs(self, client, step_geometry):
        response = client.post("/dfm/evaluate", json={
            "geometry": step_geometry,
            "inputs": {
                "process": "injection_molding",
                "material": "ABS",
                "surface_finish": "polished",
                "tolerances": [
                    {"label": "bore", "feature_size_mm": 8.0,
                     "requested_tolerance_mm": 0.01}
                ],
            },
        })
        assert response.status_code == 200
        body = response.json()
        assert body["inputs"]["material_resolved"] == "abs"
        assert [p["process"] for p in body["processes"]] == ["injection_molding"]

    def test_works_with_mocked_rib_and_boss_arrays(
        self, client, step_geometry_with_features
    ):
        step_geometry_with_features["ribs"][0]["thickness"] = 2.4
        response = client.post(
            "/dfm/evaluate",
            json={"geometry": step_geometry_with_features,
                  "inputs": {"process": "injection_molding", "material": "ABS"}},
        )
        assert response.status_code == 200
        rules = {r["rule_id"]: r for r in response.json()["processes"][0]["rule_results"]}
        assert rules["M5"]["status"] == "fail"
        assert rules["M6"]["status"] == "pass"

    def test_missing_feature_arrays_are_not_assessed(
        self, client, geometry_without_features
    ):
        response = client.post(
            "/dfm/evaluate",
            json={"geometry": geometry_without_features,
                  "inputs": {"process": "injection_molding"}},
        )
        rules = {r["rule_id"]: r for r in response.json()["processes"][0]["rule_results"]}
        assert rules["M5"]["status"] == "not_assessed"
        assert rules["M6"]["status"] == "not_assessed"
        assert rules["M5"]["score_impact"] == 0.0

    def test_rejects_a_request_without_geometry(self, client):
        assert client.post("/dfm/evaluate", json={}).status_code == 422

    def test_rejects_unknown_input_fields(self, client, step_geometry):
        response = client.post("/dfm/evaluate", json={
            "geometry": step_geometry,
            "inputs": {"materiel": "ABS"},
        })
        assert response.status_code == 422


class TestStoredReportEndpoint:
    def test_returns_a_stored_report(self, client, step_geometry):
        report = run_dfm_analysis(step_geometry).model_dump(mode="json")
        with patch.object(main, "get_analysis_by_id",
                          return_value={"results_json": {"dfm_report": report}}):
            response = client.get("/analysis/abc-123/dfm")
        assert response.status_code == 200
        assert response.json()["report_version"] == report["report_version"]

    def test_404_when_the_analysis_is_unknown(self, client):
        with patch.object(main, "get_analysis_by_id", return_value=None):
            assert client.get("/analysis/nope/dfm").status_code == 404

    def test_409_when_the_analysis_is_not_completed(self, client, step_geometry):
        report = run_dfm_analysis(step_geometry).model_dump(mode="json")
        with patch.object(main, "get_analysis_by_id",
                          return_value={
                              "status": "processing",
                              "results_json": {"dfm_report": report},
                          }):
            response = client.get("/analysis/abc-123/dfm")
        assert response.status_code == 409
        assert "only answers from completed" in response.json()["error"]["message"]

    def test_404_when_the_analysis_predates_the_rule_engine(self, client):
        with patch.object(main, "get_analysis_by_id",
                          return_value={"results_json": {"geometry_data": {}}}):
            response = client.get("/analysis/old/dfm")
        assert response.status_code == 404
        assert "no DFM report" in response.json()["error"]["message"]


class TestReportDownloadEndpoint:
    def test_downloads_a_stored_pdf_report(self, client, step_geometry):
        report = run_dfm_analysis(step_geometry).model_dump(mode="json")
        stored = {
            "status": "completed",
            "results_json": {
                "analysis_id": "abc-123",
                "filename": "bracket.stl",
                "status": "completed",
                "manufacturability_score": report["manufacturability_score"],
                "summary": "Stored report summary.",
                "dfm_report": report,
            },
        }
        with patch.object(main, "get_analysis_by_id", return_value=stored):
            response = client.post(
                "/analysis/report.pdf",
                json={
                    "analysis": stored["results_json"],
                    "include_comparison": True,
                    "material": "pla",
                    "process": "printing",
                    "tolerance": "standard"
                }
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "bracket-dfm-report.pdf" in response.headers["content-disposition"]
        assert response.content.startswith(b"%PDF-1.4")
        assert b"Manufacturability report" in response.content

    def test_downloads_an_inline_pdf_report(self, client, step_geometry):
        report = run_dfm_analysis(step_geometry).model_dump(mode="json")
        response = client.post(
            "/analysis/report.pdf",
            json={
                "include_comparison": False,
                "analysis": {
                    "analysis_id": "abc-123",
                    "filename": "inline.stl",
                    "status": "completed",
                    "manufacturability_score": report["manufacturability_score"],
                    "summary": "Inline report summary.",
                    "dfm_report": report,
                    "issues": [],
                },
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "inline-dfm-report.pdf" in response.headers["content-disposition"]
        assert response.content.startswith(b"%PDF-1.4")

    def test_rejects_inline_pdf_without_completed_analysis(self, client):
        response = client.post(
            "/analysis/report.pdf",
            json={"analysis": {"filename": "part.stl", "status": "processing"}},
        )

        assert response.status_code == 409
        assert "completed analysis" in response.json()["error"]["message"]


class TestAIAskEndpoint:
    def _report(self, geometry, **kwargs):
        return run_dfm_analysis(geometry, DFMInputs(**kwargs)).model_dump(mode="json")

    def test_answers_from_an_inline_report(self, client, stl_geometry):
        report = self._report(stl_geometry, process=ProcessType.printing)
        response = client.post("/ai/ask", json={
            "question": "Why is this part not manufacturable?",
            "report": report,
        })
        assert response.status_code == 200
        body = response.json()
        assert "P2" in body["answer"]
        assert body["mode"] == "deterministic"

    def test_answers_from_a_stored_analysis(self, client, stl_geometry):
        stored = {
            "results_json": {
                "dfm_report": self._report(stl_geometry, process=ProcessType.printing),
                "geometry_data": stl_geometry,
            }
        }
        with patch.object(main, "get_analysis_by_id", return_value=stored):
            response = client.post("/ai/ask", json={
                "question": "Which rules failed?", "analysis_id": "abc-123",
            })
        assert response.status_code == 200
        assert response.json()["analysis_id"] == "abc-123"

    def test_refuses_to_analyse_when_no_report_exists(self, client, stl_geometry):
        """The AI must never rerun geometry or the DFM rules to fill a gap."""
        with patch.object(main, "get_analysis_by_id",
                          return_value={"results_json": {"geometry_data": stl_geometry}}):
            response = client.post("/ai/ask", json={
                "question": "Why is this not manufacturable?", "analysis_id": "abc-123",
            })
        assert response.status_code == 409
        assert "does not compute it" in response.json()["error"]["message"]

    def test_refuses_to_answer_from_a_processing_analysis(self, client, stl_geometry):
        stored = {
            "status": "processing",
            "results_json": {
                "dfm_report": self._report(stl_geometry, process=ProcessType.printing),
                "geometry_data": stl_geometry,
            },
        }
        with patch.object(main, "get_analysis_by_id", return_value=stored):
            response = client.post("/ai/ask", json={
                "question": "Which rules failed?", "analysis_id": "abc-123",
            })
        assert response.status_code == 409
        assert "not completed" in response.json()["error"]["message"]

    def test_requires_a_report_or_an_analysis_id(self, client):
        response = client.post("/ai/ask", json={"question": "Why?"})
        assert response.status_code == 422

    def test_rejects_an_empty_question(self, client, stl_geometry):
        response = client.post("/ai/ask", json={
            "question": "", "report": self._report(stl_geometry),
        })
        assert response.status_code == 422

    def test_rejects_a_malformed_report(self, client):
        response = client.post("/ai/ask", json={
            "question": "Why?", "report": {"not": "a report"},
        })
        assert response.status_code == 422

    @pytest.mark.parametrize("question", [
        "Why is this part not manufacturable?",
        "Which rules failed?",
        "How can the design be improved?",
        "Why is one manufacturing process preferred?",
    ])
    def test_answers_the_four_product_questions(self, client, stl_geometry, question):
        response = client.post("/ai/ask", json={
            "question": question, "report": self._report(stl_geometry),
        })
        assert response.status_code == 200
        assert len(response.json()["answer"]) > 40


class TestExistingRoutesStillWork:
    def test_health_check(self, client):
        assert client.get("/").status_code == 200

    def test_analyze_mock_unchanged(self, client):
        body = client.post("/analyze-mock").json()
        assert body["analysis_id"] == "mock-analysis-0001"
