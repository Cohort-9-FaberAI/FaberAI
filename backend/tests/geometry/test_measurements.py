"""
Unit tests for geometry.measurements / geometry.loaders.

Per the spec: cube, cylinder, sphere, hollow box — each checked against
its analytical ground truth.

The mesh (.stl / trimesh) path always runs. The OCC (.step) path is
skipped automatically if pythonOCC isn't installed in this environment,
so this file is safe to run on machines without OpenCASCADE set up yet.
"""

import math

import numpy as np
import pytest
import trimesh

from geometry.loaders import load_geometry
from geometry.measurements import (
    compute_bbox_mesh,
    compute_oriented_bbox_mesh,
    compute_volume_mesh,
    compute_surface_area_mesh,
    compute_center_mass_mesh,
)

try:
    import OCC.Core  # noqa: F401

    HAS_OCC = True
except ImportError:
    HAS_OCC = False

REL_TOL = 1e-6          # exact primitives (cube, hollow box)
TESSELLATION_TOL = 0.02  # 2% — curved primitives (cylinder, sphere) are
                         # tessellated meshes, so exact match isn't expected
OCC_BBOX_ATOL = 1e-5    # OCC's Bnd_Box adds a small internal safety gap
                        # (observed ~1e-7), so corners aren't bit-exact zero


@pytest.fixture
def cube():
    """10 x 10 x 10 mm cube, corner at origin."""
    mesh = trimesh.creation.box(extents=[10, 10, 10])
    mesh.apply_translation([5, 5, 5])
    return mesh, {
        "bbox_min": [0, 0, 0],
        "bbox_max": [10, 10, 10],
        "volume": 1000.0,
        "area": 600.0,
        "center_mass": [5, 5, 5],
    }


@pytest.fixture
def cylinder():
    """Radius 5 mm, height 20 mm cylinder, base centered at origin."""
    radius, height = 5.0, 20.0
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=128)
    mesh.apply_translation([0, 0, height / 2])
    return mesh, {
        "volume": math.pi * radius**2 * height,
        "area": 2 * math.pi * radius * height + 2 * math.pi * radius**2,
        "center_mass": [0, 0, height / 2],
    }


@pytest.fixture
def sphere():
    """Radius 5 mm sphere, centered at origin."""
    radius = 5.0
    mesh = trimesh.creation.icosphere(subdivisions=4, radius=radius)
    return mesh, {
        "volume": (4 / 3) * math.pi * radius**3,
        "area": 4 * math.pi * radius**2,
        "center_mass": [0, 0, 0],
    }


@pytest.fixture
def hollow_box():
    """20mm outer cube with a 10mm concentric cube cavity (wall = 5mm)."""
    outer = trimesh.creation.box(extents=[20, 20, 20])
    inner = trimesh.creation.box(extents=[10, 10, 10])
    mesh = outer.difference(inner)
    return mesh, {
        "volume": 20**3 - 10**3,  # 7000
        "center_mass": [0, 0, 0],  # symmetric, so centroid stays at origin
    }


def test_cube_mesh(cube):
    mesh, expected = cube
    bb = compute_bbox_mesh(mesh)
    assert np.allclose(bb.min_corner, expected["bbox_min"])
    assert np.allclose(bb.max_corner, expected["bbox_max"])
    assert bb.width == bb.depth == bb.height == 10.0
    assert math.isclose(compute_volume_mesh(mesh), expected["volume"], rel_tol=REL_TOL)
    assert math.isclose(compute_surface_area_mesh(mesh), expected["area"], rel_tol=REL_TOL)
    assert np.allclose(compute_center_mass_mesh(mesh), expected["center_mass"])


def test_cube_moment_of_inertia(cube):
    from geometry.measurements import compute_moment_inertia_mesh

    mesh, expected = cube
    I = compute_moment_inertia_mesh(mesh)
    assert I.shape == (3, 3)
    # Analytical solid-cube inertia about center of mass: (1/6) * m * s^2
    # on the diagonal, density=1 (mesh volume IS the mass here), zero
    # off-diagonal since the cube is symmetric about its own axes.
    expected_diag = (1 / 6) * expected["volume"] * 10.0**2
    assert math.isclose(I[0, 0], expected_diag, rel_tol=REL_TOL)
    assert math.isclose(I[1, 1], expected_diag, rel_tol=REL_TOL)
    assert math.isclose(I[2, 2], expected_diag, rel_tol=REL_TOL)
    off_diag = I - np.diag(np.diag(I))
    assert np.allclose(off_diag, 0, atol=1e-6)


def test_cube_oriented_bbox_matches_axis_aligned(cube):
    # A cube's oriented bbox should have the same extents as its AABB,
    # just potentially in a rotated frame (here: no rotation needed).
    mesh, expected = cube
    obb = compute_oriented_bbox_mesh(mesh)
    extents = obb.max_corner - obb.min_corner
    assert np.allclose(sorted(extents), [10.0, 10.0, 10.0])


def test_cylinder_mesh(cylinder):
    mesh, expected = cylinder
    assert math.isclose(
        compute_volume_mesh(mesh), expected["volume"], rel_tol=TESSELLATION_TOL
    )
    assert math.isclose(
        compute_surface_area_mesh(mesh), expected["area"], rel_tol=TESSELLATION_TOL
    )
    assert np.allclose(
        compute_center_mass_mesh(mesh), expected["center_mass"], atol=1e-2
    )


def test_sphere_mesh(sphere):
    mesh, expected = sphere
    assert math.isclose(
        compute_volume_mesh(mesh), expected["volume"], rel_tol=TESSELLATION_TOL
    )
    assert math.isclose(
        compute_surface_area_mesh(mesh), expected["area"], rel_tol=TESSELLATION_TOL
    )
    assert np.allclose(
        compute_center_mass_mesh(mesh), expected["center_mass"], atol=1e-6
    )


def test_hollow_box_mesh(hollow_box):
    mesh, expected = hollow_box
    assert math.isclose(compute_volume_mesh(mesh), expected["volume"], rel_tol=1e-3)
    assert np.allclose(compute_center_mass_mesh(mesh), expected["center_mass"], atol=1e-6)


def test_reliability_flag_on_good_mesh(cube):
    from geometry.measurements import compute_volume_mesh, is_mesh_reliable

    mesh, expected = cube
    compute_volume_mesh(mesh)  # populates/repairs in place before the check
    assert is_mesh_reliable(mesh) is True


def test_reliability_flag_catches_unrepairable_damage():
    """A mesh missing a large chunk of its surface can't be fully patched
    by fill_holes() — measurements_reliable should end up False so callers
    don't silently trust a meaningless volume (this mirrors a real fixture
    file, e.g. 100026.stl, that came back watertight=False even after
    fix_normals()+fill_holes())."""
    from geometry.measurements import compute_volume_mesh, is_mesh_reliable

    mesh = trimesh.creation.icosphere(subdivisions=2, radius=5)
    # Remove a large contiguous patch of faces (not just one triangle) to
    # simulate real structural damage that fill_holes() can't fix.
    keep = int(len(mesh.faces) * 0.7)
    mesh.faces = mesh.faces[:keep]
    mesh.remove_unreferenced_vertices()

    compute_volume_mesh(mesh)  # attempts repair, but damage is too large
    assert is_mesh_reliable(mesh) is False


def test_load_geometry_stl_end_to_end(cube, tmp_path):
    mesh, expected = cube
    path = tmp_path / "cube.stl"
    mesh.export(path)

    model = load_geometry(str(path))
    assert model.source_format.value == "stl"
    assert math.isclose(model.volume_mm3, expected["volume"], rel_tol=REL_TOL)
    assert math.isclose(model.surface_area_mm2, expected["area"], rel_tol=REL_TOL)
    assert np.allclose(model.center_mass, expected["center_mass"])



@pytest.mark.skipif(not HAS_OCC, reason="pythonOCC not installed in this environment")
class TestOccPath:
    """Same solids, generated via OCC's BRepPrimAPI, checked via the OCC
    measurement functions. Requires pythonOCC / OpenCASCADE."""

    def test_cube_occ(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from geometry.measurements import (
            compute_bbox_occ,
            compute_volume_occ,
            compute_surface_area_occ,
            compute_center_mass_occ,
        )

        shape = BRepPrimAPI_MakeBox(10, 10, 10).Shape()
        bb = compute_bbox_occ(shape)
        assert np.allclose(bb.min_corner, [0, 0, 0], atol=OCC_BBOX_ATOL)
        assert np.allclose(bb.max_corner, [10, 10, 10], atol=OCC_BBOX_ATOL)
        assert math.isclose(compute_volume_occ(shape), 1000.0, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), 600.0, rel_tol=REL_TOL)
        assert np.allclose(compute_center_mass_occ(shape), [5, 5, 5])

        from geometry.measurements import compute_moment_inertia_occ
        I = compute_moment_inertia_occ(shape)
        expected_diag = (1 / 6) * 1000.0 * 10.0**2
        assert I.shape == (3, 3)
        assert math.isclose(I[0, 0], expected_diag, rel_tol=1e-3)
        assert math.isclose(I[1, 1], expected_diag, rel_tol=1e-3)
        assert math.isclose(I[2, 2], expected_diag, rel_tol=1e-3)

    def test_cylinder_occ(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeCylinder
        from geometry.measurements import compute_volume_occ, compute_surface_area_occ

        radius, height = 5.0, 20.0
        shape = BRepPrimAPI_MakeCylinder(radius, height).Shape()
        expected_vol = math.pi * radius**2 * height
        expected_area = 2 * math.pi * radius * height + 2 * math.pi * radius**2
        assert math.isclose(compute_volume_occ(shape), expected_vol, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), expected_area, rel_tol=REL_TOL)

    def test_sphere_occ(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
        from geometry.measurements import compute_volume_occ, compute_surface_area_occ

        radius = 5.0
        shape = BRepPrimAPI_MakeSphere(radius).Shape()
        expected_vol = (4 / 3) * math.pi * radius**3
        expected_area = 4 * math.pi * radius**2
        assert math.isclose(compute_volume_occ(shape), expected_vol, rel_tol=REL_TOL)
        assert math.isclose(compute_surface_area_occ(shape), expected_area, rel_tol=REL_TOL)

    def test_hollow_box_occ(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut
        from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_Vec
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
        from geometry.measurements import compute_volume_occ

        outer = BRepPrimAPI_MakeBox(20, 20, 20).Shape()
        inner_raw = BRepPrimAPI_MakeBox(10, 10, 10).Shape()

        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(5, 5, 5))  # center the 10mm cavity
        inner = BRepBuilderAPI_Transform(inner_raw, trsf, True).Shape()

        hollow = BRepAlgoAPI_Cut(outer, inner).Shape()
        assert math.isclose(compute_volume_occ(hollow), 20**3 - 10**3, rel_tol=1e-6)