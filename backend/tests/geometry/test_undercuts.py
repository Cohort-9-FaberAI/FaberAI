"""
Tests for geometry.features.undercuts — Stage 1 (single pull direction,
shadow/reachability detection, without side-action releasability yet).

Three cases, chosen specifically to catch the classic false-positive trap:
- A plain box must show ZERO undercuts (a naive "does the face point
  backward" test would wrongly flag the bottom face here).
- A box with a horizontal tunnel through it must show undercuts on BOTH
  inner tunnel faces, for a vertical pull.
- The SAME tunnel shape must show ZERO undercuts when pulled along the
  tunnel's own axis instead — demonstrating undercuts are genuinely
  pull-direction-dependent, not a fixed property of the geometry alone.
"""

import glob
from pathlib import Path

import pytest
from build123d import Box

from geometry.features.undercuts import (
    find_undercut_candidate_faces,
    detect_undercuts,
    classify_face_zone,
    _connected_components,
)


def test_plain_box_has_no_undercuts():
    """Sanity check against the classic false-positive: a naive per-face
    'does the normal point backward' test would wrongly flag a box's
    bottom face. The shadow test must correctly find nothing."""
    shape = Box(50, 50, 40)
    undercuts = detect_undercuts(shape, pull_direction=[0, 0, 1])
    assert undercuts == []


def test_horizontal_tunnel_has_undercuts_for_vertical_pull():
    """A box with a horizontal tunnel through it: pulling vertically,
    BOTH inner tunnel surfaces (floor and ceiling) are undercuts — the
    whole tunnel needs a horizontal side-action to form at all."""
    block = Box(50, 50, 40)
    tunnel = Box(60, 15, 15)
    shape = block - tunnel

    undercuts = detect_undercuts(shape, pull_direction=[0, 0, 1])
    assert len(undercuts) == 2

    all_face_ids = set()
    for u in undercuts:
        all_face_ids.update(u.face_ids)
        assert u.center is not None
    # each undercut group should be a single face here (floor, ceiling
    # aren't adjacent to each other -- they only touch the tunnel's
    # non-shadowed side walls)
    assert all(len(u.face_ids) == 1 for u in undercuts)


def test_same_tunnel_has_no_undercuts_along_its_own_axis():
    """The exact same geometry as above, but pulled along the tunnel's
    own axis instead of vertically -- a straight bore parallel to the
    pull direction is never an undercut. This is the key
    pull-direction-dependence check the feature spec calls out."""
    block = Box(50, 50, 40)
    tunnel = Box(60, 15, 15)
    shape = block - tunnel

    undercuts = detect_undercuts(shape, pull_direction=[1, 0, 0])
    assert undercuts == []


def test_classify_face_zone():
    import numpy as np

    pull = np.array([0.0, 0.0, 1.0])
    assert classify_face_zone(np.array([0, 0, 1.0]), pull) == "cavity"
    assert classify_face_zone(np.array([0, 0, -1.0]), pull) == "core"
    assert classify_face_zone(np.array([1.0, 0, 0]), pull) == "side"


def test_connected_components_grouping():
    """Isolated check that adjacent shadowed faces merge into one group,
    while non-adjacent (or adjacent-only-via-non-shadowed-faces) ones
    stay separate."""
    adjacency = {
        0: {1}, 1: {0, 2}, 2: {1},
        5: {6, 7},   # 6, 7 are not shadowed, so 5 stays isolated
        8: {9}, 9: {8},
    }
    shadowed = {0, 1, 2, 5, 8, 9}

    components = _connected_components(shadowed, adjacency)
    component_sets = sorted([sorted(c) for c in components])
    assert component_sets == [[0, 1, 2], [5], [8, 9]]


def test_undercut_candidate_faces_reports_zone_for_every_face():
    """find_undercut_candidate_faces (the lower-level, pre-grouping
    function) should report exactly one result per face, covering all
    faces regardless of whether they're shadowed."""
    shape = Box(50, 50, 40)
    results = find_undercut_candidate_faces(shape, pull_direction=[0, 0, 1])
    assert len(results) == len(shape.faces())
    zones = {r.zone for r in results}
    assert zones == {"cavity", "core", "side"}


# ---------------------------------------------------------------------------
# Real fixture files
# ---------------------------------------------------------------------------
# The synthetic tests above prove the algorithm is CORRECT (catches the
# false-positive trap, finds genuine undercuts, respects pull-direction
# dependence). This section proves the pipeline doesn't CRASH on real,
# messier STEP files -- a different, complementary kind of confidence.
#
# Most of the pre-existing fixtures were built for other feature types
# (holes, fillets, bosses, cavities) and don't happen to contain a real
# undercut -- that's expected, not a bug. known_undercut.step is the one
# fixture deliberately built with a known, verified undercut (the same
# tunnel-block shape from the synthetic tests above, exported to a real
# .step file), so THAT one gets checked for an exact expected result.

try:
    from build123d import import_step
    HAS_BUILD123D = True
except ImportError:
    HAS_BUILD123D = False

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_STEP_FILES = sorted(glob.glob(str(FIXTURES_DIR / "*.step"))) + \
                      sorted(glob.glob(str(FIXTURES_DIR / "*.stp")))


@pytest.mark.skipif(not HAS_BUILD123D, reason="build123d not installed in this environment")
@pytest.mark.skipif(not FIXTURE_STEP_FILES, reason="no fixture STEP files found")
@pytest.mark.parametrize("step_path", FIXTURE_STEP_FILES, ids=lambda p: Path(p).name)
def test_undercuts_do_not_crash_on_real_fixtures(step_path):
    """Every real STEP fixture must run through detect_undercuts() without
    raising -- regardless of how many (if any) undercuts it actually
    contains. A crash here means a real geometric edge case the synthetic
    tests didn't cover."""
    shape = import_step(step_path)
    undercuts = detect_undercuts(shape, pull_direction=[0, 0, 1])
    assert isinstance(undercuts, list)
    for u in undercuts:
        assert u.center is not None
        assert len(u.face_ids) > 0


@pytest.mark.skipif(not HAS_BUILD123D, reason="build123d not installed in this environment")
def test_known_undercut_fixture_matches_expected_result():
    """The one fixture deliberately built with a known undercut (see
    test_horizontal_tunnel_has_undercuts_for_vertical_pull above -- same
    shape, exported to a real .step file) must give the exact same
    result loaded from disk as it does built directly in code."""
    path = FIXTURES_DIR / "known_undercut.step"
    if not path.exists():
        pytest.skip(
            "known_undercut.step not present in fixtures/ -- see "
            "test_horizontal_tunnel_has_undercuts_for_vertical_pull for "
            "how to regenerate it (Box(50,50,40) - Box(60,15,15), "
            "exported via build123d.export_step)."
        )

    shape = import_step(str(path))

    vertical = detect_undercuts(shape, pull_direction=[0, 0, 1])
    assert len(vertical) == 2

    along_tunnel_axis = detect_undercuts(shape, pull_direction=[1, 0, 0])
    assert along_tunnel_axis == []