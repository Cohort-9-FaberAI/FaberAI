"""
Tests for the STEP-side measurement functions (bbox, volume, area,
centroid, inertia) against real build123d/OCP geometry.

Replaces the old TestOccPath class (which built shapes via pythonocc-core's
BRepPrimAPI and is no longer valid — the measurement functions were
rewritten to use OCP, since the dispatcher's primary STEP path loads via
build123d, and OCP/OCC.Core shape objects are incompatible, different
compiled types despite both wrapping OpenCASCADE).

Skips automatically if build123d isn't installed, so this file doesn't
break environments that only have the mesh/STL path set up.
"""

import math

import numpy as np
import pytest

try:
    from build123d import Box, Cylinder, Sphere
    HAS_BUILD123D = True
except ImportError:
    HAS_BUILD123D = False

from geometry.measurements import (
    compute_bbox_occ,
    compute_volume_occ,
    compute_surface_area_occ,
    compute_center_mass_occ,
    compute_moment_inertia_occ,
)

REL_TOL = 1e-6
OCP_BBOX_ATOL = 1e-4  # OCP's Bnd_Box adds a small internal safety gap,
                      # same as pythonocc-core did, so corners aren't
                      # bit-exact


@pytest.mark.skipif(not HAS_BUILD123D, reason="build123d not installed in this environment")
class TestCoreMeasurementsOcc:
    """Cube, cylinder, sphere, hollow box — via build123d/OCP."""

    def test_cube(self):
        shape = Box(10, 10, 10)  # build123d centers shapes at the origin
        bb = compute_bbox_occ(shape)
        assert np.allclose(bb.min_corner, [-5, -5, -5], atol=OCP_BBOX_ATOL)
        assert np.allclose(bb.max_corner, [5, 5, 5], atol=OCP_BBOX_ATOL)
        assert math.isclose(compute_volume_occ(shape), 1000.0, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), 600.0, rel_tol=REL_TOL)
        assert np.allclose(compute_center_mass_occ(shape), [0, 0, 0], atol=1e-6)

        I = compute_moment_inertia_occ(shape)
        expected_diag = (1 / 6) * 1000.0 * 10.0**2
        assert I.shape == (3, 3)
        assert math.isclose(I[0, 0], expected_diag, rel_tol=1e-3)
        assert math.isclose(I[1, 1], expected_diag, rel_tol=1e-3)
        assert math.isclose(I[2, 2], expected_diag, rel_tol=1e-3)

    def test_cylinder(self):
        radius, height = 5.0, 20.0
        shape = Cylinder(radius=radius, height=height)
        expected_vol = math.pi * radius**2 * height
        expected_area = 2 * math.pi * radius * height + 2 * math.pi * radius**2
        assert math.isclose(compute_volume_occ(shape), expected_vol, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), expected_area, rel_tol=REL_TOL)

    def test_sphere(self):
        radius = 5.0
        shape = Sphere(radius=radius)
        expected_vol = (4 / 3) * math.pi * radius**3
        expected_area = 4 * math.pi * radius**2
        assert math.isclose(compute_volume_occ(shape), expected_vol, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), expected_area, rel_tol=REL_TOL)

    def test_hollow_box(self):
        outer = Box(20, 20, 20)
        inner = Box(10, 10, 10)
        hollow = outer - inner
        assert math.isclose(compute_volume_occ(hollow), 20**3 - 10**3, rel_tol=1e-6)
        assert np.allclose(compute_center_mass_occ(hollow), [0, 0, 0], atol=1e-6)