from dfm.models import Finding, GeometryRef, Vector3 as DFMVector3, Severity
from app.schemas import Vector3 as AppVector3
from core.workers import _finding_to_issue


def test_finding_to_issue_falls_back_to_bbox_center_when_centroid_missing():
    finding = Finding(
        finding_id="test-1",
        rule_id="M1",
        severity=Severity.major,
        message="Missing centroid should use bbox center",
        recommendation="Fix the face location",
        geometry_ref=GeometryRef(
            face_ids=[1],
            bbox_min=DFMVector3(x=1.0, y=2.0, z=3.0),
            bbox_max=DFMVector3(x=5.0, y=6.0, z=7.0),
            centroid=None,
        ),
    )

    issue = _finding_to_issue(finding, "M1")

    assert issue.three_js_highlight.center == AppVector3(x=3.0, y=4.0, z=5.0)
    assert issue.three_js_highlight.min == AppVector3(x=1.0, y=2.0, z=3.0)
    assert issue.three_js_highlight.max == AppVector3(x=5.0, y=6.0, z=7.0)
