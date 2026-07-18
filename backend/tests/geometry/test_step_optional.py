"""
Tests for optional STEP dependency handling.

STEP support (pythonocc-core / build123d) is optional. These tests simulate
an environment where those packages are missing and verify that:
  * geometry.loaders still imports (so app startup can't fail on them),
  * STEP loads fail with a clear StepSupportUnavailableError,
  * the STL path keeps working.

They pass regardless of whether the optional packages are actually installed:
the fixture blocks the imports either way.
"""

import importlib
import sys

import pytest
import trimesh

from geometry.loaders import StepSupportUnavailableError, load_geometry

OPTIONAL_STEP_PACKAGES = ("OCC", "build123d")


@pytest.fixture
def without_step_deps(monkeypatch):
    """Simulate an environment with no optional STEP dependencies installed.

    Drops any already-imported OCC/build123d modules and blocks re-imports by
    mapping the top-level packages to None in sys.modules (the import system
    then raises ImportError). monkeypatch restores everything on teardown.
    """
    for name in list(sys.modules):
        if name.split(".")[0] in OPTIONAL_STEP_PACKAGES:
            monkeypatch.delitem(sys.modules, name)
    for name in OPTIONAL_STEP_PACKAGES:
        monkeypatch.setitem(sys.modules, name, None)


def test_loaders_package_imports_without_step_deps(without_step_deps, monkeypatch):
    """The app must import (and therefore start) without STEP dependencies."""
    for name in list(sys.modules):
        if name == "geometry.loaders" or name.startswith("geometry.loaders."):
            monkeypatch.delitem(sys.modules, name)

    module = importlib.import_module("geometry.loaders")

    assert hasattr(module, "load_geometry")
    assert hasattr(module, "StepSupportUnavailableError")


def test_step_load_fails_gracefully(without_step_deps, tmp_path):
    step_file = tmp_path / "part.step"
    step_file.write_text("ISO-10303-21;")

    with pytest.raises(StepSupportUnavailableError, match="pythonocc-core"):
        load_geometry(str(step_file))


def test_stp_extension_fails_gracefully(without_step_deps, tmp_path):
    stp_file = tmp_path / "part.stp"
    stp_file.write_text("ISO-10303-21;")

    with pytest.raises(StepSupportUnavailableError, match="STEP support is unavailable"):
        load_geometry(str(stp_file))


def test_legacy_build123d_loader_fails_gracefully(without_step_deps, tmp_path):
    from geometry.loaders.step_loader import load_step as legacy_load_step

    with pytest.raises(StepSupportUnavailableError, match="build123d"):
        legacy_load_step(str(tmp_path / "part.step"))


def test_stl_path_unaffected_by_missing_step_deps(without_step_deps, tmp_path):
    mesh = trimesh.creation.box(extents=[10, 10, 10])
    path = tmp_path / "cube.stl"
    mesh.export(path)

    model = load_geometry(str(path))

    assert model.source_format.value == "stl"
    assert model.volume_mm3 == pytest.approx(1000.0)
