"""Check a running local stack using only Python's standard library."""

import argparse
import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url, data=None, content_type=None, timeout=60):
    headers = {"Content-Type": content_type} if content_type else {}
    with urlopen(Request(url, data=data, headers=headers), timeout=timeout) as response:
        return response.read()


def smoke_test(api_url, web_url, file, timeout):
    fetch(f"{api_url}/health/dependencies")
    if b'<div id="root">' not in fetch(web_url):
        raise RuntimeError("Frontend did not return the application HTML.")
    # A nested URL must also work when refreshed (React Router SPA fallback).
    if b'<div id="root">' not in fetch(f"{web_url}/projects"):
        raise RuntimeError("Frontend route refresh failed.")
    print("Frontend and analysis dependencies are ready.")

    boundary = uuid.uuid4().hex
    content = file.read_bytes()
    if '"' in file.name or "\r" in file.name or "\n" in file.name:
        raise ValueError("Unsupported filename for the smoke-test upload.")
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    upload = json.loads(fetch(f"{api_url}/upload/", body, f"multipart/form-data; boundary={boundary}"))
    print(f"Uploaded {file.name}; waiting for CAD analysis.")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = json.loads(fetch(
            f"{api_url}/tasks/{upload['task_id']}?analysis_id={upload['analysis_id']}"
        ))
        if result["status"] in {"FAILED", "FAILURE"}:
            raise RuntimeError("Analysis failed; check docker compose logs worker.")
        if result["status"] == "SUCCESS":
            analysis = result.get("result")
            if not analysis or not analysis.get("dfm_report"):
                raise RuntimeError("Analysis completed without a manufacturability report.")
            break
        time.sleep(1)
    else:
        raise TimeoutError(f"Analysis did not finish within {timeout} seconds.")

    if fetch(upload["source_file_url"]) != content:
        raise RuntimeError("Stored upload does not match the original CAD file.")
    if not analysis.get("file_url") or not fetch(analysis["file_url"]):
        raise RuntimeError("3D preview is unavailable.")
    print("CAD analysis, persisted results, and 3D preview passed.")

    pdf = fetch(
        f"{api_url}/analysis/report.pdf",
        json.dumps({"analysis": analysis, "inline": True}).encode(), "application/json",
    )
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError("Report endpoint did not return a PDF.")
    report = json.loads(fetch(f"{api_url}/analysis/{upload['analysis_id']}/dfm"))
    if not report.get("processes"):
        raise RuntimeError("Stored DFM report has no process findings.")
    answer = json.loads(fetch(
        f"{api_url}/ai/ask",
        json.dumps({"analysis_id": upload["analysis_id"], "question": "What should I fix?"}).encode(),
        "application/json",
    ))
    if not answer.get("answer"):
        raise RuntimeError("Report Q&A returned no answer.")
    print(f"PDF preview/export and report Q&A passed ({answer['mode']}).")
    print(f"Smoke test passed. Analysis ID: {upload['analysis_id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=f"http://127.0.0.1:{os.environ.get('FABERAI_API_PORT', '8000')}")
    parser.add_argument("--web-url", default=f"http://127.0.0.1:{os.environ.get('FABERAI_WEB_PORT', '5173')}")
    parser.add_argument("--file", type=Path, default=Path(__file__).resolve().parents[1] / "frontend/public/faberai-sample-part.stl")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    try:
        smoke_test(args.api_url.rstrip("/"), args.web_url.rstrip("/"), args.file, args.timeout)
    except (HTTPError, URLError, OSError, RuntimeError, ValueError, KeyError) as exc:
        parser.exit(1, f"Smoke test failed: {exc}\nCheck docker compose ps and docker compose logs api worker.\n")
