"""
Tests for geometry.features (cylindrical manufacturing feature detection).

Covers exactly the synthetic cases requested in the feature spec:
- Cube with a through hole
- Cube with a blind hole
- Plate with a boss
- Plate with two bosses
- Plate with a (rectangular) pocket

Plus one extra case (counterbore) since the pipeline supports it and it's
cheap to verify given the infrastructure is already built.

All fixtures are built directly with build123d (no external file needed) so
this test suite runs anywhere build123d installs — no pythonOCC/conda
required, since build123d bundles its own OCP binding.
"""

import math

import numpy as np
from build123d import Box, Cylinder, Pos

from geometry.measurements.face_graph import build_face_graph
from geometry.measurements.face_extraction import graph_to_faces_and_edges
from geometry.features.holes import detect_holes
from geometry.features.bosses import detect_bosses_full
from geometry.features.cavities import detect_cavities_full

REL_TOL = 1e-6


def _faces_and_edges(shape):
    graph = build_face_graph(shape.faces(), shape)
    return graph_to_faces_and_edges(graph, None, None)


def test_through_hole():
    """50x50x40 block, through-hole radius 5 along Z."""
    shape = Box(50, 50, 40) - Cylinder(radius=5, height=60)
    faces, edges = _faces_and_edges(shape)

    holes = detect_holes(faces, edges)
    assert len(holes) == 1

    h = holes[0]
    assert h.type == "through"
    assert h.through is True
    assert math.isclose(h.diameter, 10.0, rel_tol=REL_TOL)
    assert math.isclose(h.depth, 40.0, rel_tol=REL_TOL)
    assert np.allclose(np.abs(h.axis), [0, 0, 1])
    assert math.isclose(h.volume_removed(), math.pi * 5**2 * 40, rel_tol=1e-3)
    assert math.isclose(h.aspect_ratio(), 40 / 10, rel_tol=1e-3)


def test_blind_hole():
    """50x50x40 block, blind hole radius 5, depth 15 from the top."""
    shape = Box(50, 50, 40) - Pos(0, 0, 20 - 7.5) * Cylinder(radius=5, height=15)
    faces, edges = _faces_and_edges(shape)

    holes = detect_holes(faces, edges)
    assert len(holes) == 1

    h = holes[0]
    assert h.type == "blind"
    assert h.through is False
    assert math.isclose(h.diameter, 10.0, rel_tol=REL_TOL)
    assert math.isclose(h.depth, 15.0, rel_tol=1e-3)
    assert h.bottom_face is not None
    assert h.entry_face is not None


def test_counterbore_hole():
    """Through-hole radius 3, with a wider radius-6 recess 8mm deep from the top."""
    block = Box(50, 50, 40)
    narrow = Cylinder(radius=3, height=60)
    wide = Pos(0, 0, 20 - 4) * Cylinder(radius=6, height=8)
    shape = block - narrow - wide
    faces, edges = _faces_and_edges(shape)

    holes = detect_holes(faces, edges)
    assert len(holes) == 1

    h = holes[0]
    assert h.type == "counterbore"
    assert math.isclose(h.diameter, 6.0, rel_tol=1e-3)       # primary (narrow) bore
    assert math.isclose(h.depth, 40.0, rel_tol=1e-3)         # full through-span
    assert math.isclose(h.secondary_diameter, 12.0, rel_tol=1e-3)
    assert math.isclose(h.secondary_depth, 8.0, rel_tol=1e-3)


def test_no_holes_on_plain_block():
    """A featureless block should detect zero holes."""
    shape = Box(50, 50, 40)
    faces, edges = _faces_and_edges(shape)
    assert detect_holes(faces, edges) == []


def test_single_boss():
    """Plate with one boss, radius 8, height 15, sitting flush on top."""
    plate = Box(50, 50, 10)  # spans z=-5..5
    boss_height = 15
    boss = Pos(0, 0, 5 + boss_height / 2) * Cylinder(radius=8, height=boss_height)
    shape = plate + boss
    faces, edges = _faces_and_edges(shape)

    bosses = detect_bosses_full(faces, edges)
    assert len(bosses) == 1

    b = bosses[0]
    assert math.isclose(b.outer_diameter, 16.0, rel_tol=1e-3)
    assert math.isclose(b.height, 15.0, rel_tol=1e-3)
    assert b.attached_face is not None
    assert b.is_solid() is True
    assert math.isclose(b.height_ratio(), 15 / 16, rel_tol=1e-3)


def test_two_bosses():
    """Plate with two bosses of different sizes."""
    plate = Box(80, 50, 10)
    b1 = Pos(-20, 0, 5 + 15 / 2) * Cylinder(radius=8, height=15)
    b2 = Pos(20, 0, 5 + 10 / 2) * Cylinder(radius=5, height=10)
    shape = plate + b1 + b2
    faces, edges = _faces_and_edges(shape)

    bosses = detect_bosses_full(faces, edges)
    assert len(bosses) == 2

    diameters = sorted(b.outer_diameter for b in bosses)
    heights = sorted(b.height for b in bosses)
    assert math.isclose(diameters[0], 10.0, rel_tol=1e-3)
    assert math.isclose(diameters[1], 16.0, rel_tol=1e-3)
    assert math.isclose(heights[0], 10.0, rel_tol=1e-3)
    assert math.isclose(heights[1], 15.0, rel_tol=1e-3)


def test_no_bosses_on_plain_block():
    shape = Box(50, 50, 40)
    faces, edges = _faces_and_edges(shape)
    assert detect_bosses_full(faces, edges) == []


def test_rectangular_pocket():
    """50x50x20 block with a 20x15x6 rectangular pocket in the top face."""
    block = Box(50, 50, 20)
    pocket_depth = 6
    pocket = Pos(0, 0, 10 - pocket_depth / 2) * Box(20, 15, pocket_depth)
    shape = block - pocket
    faces, edges = _faces_and_edges(shape)

    cavities = detect_cavities_full(faces, edges)
    assert len(cavities) == 1

    c = cavities[0]
    assert math.isclose(c.depth, 6.0, rel_tol=1e-3)
    assert math.isclose(c.volume, 20 * 15 * 6, rel_tol=1e-3)
    assert math.isclose(c.opening_area(), 20 * 15, rel_tol=1e-3)
    assert c.opening_face is not None
    assert len(c.wall_faces) == 4  # rectangular pocket -> 4 walls
    assert len(c.bottom_faces) == 1


def test_no_cavities_on_plain_block():
    shape = Box(50, 50, 40)
    faces, edges = _faces_and_edges(shape)
    assert detect_cavities_full(faces, edges) == []

def test_hole_shape_has_no_bosses_or_cavities():
    shape = Box(50, 50, 40) - Cylinder(radius=5, height=60)
    faces, edges = _faces_and_edges(shape)
    assert len(detect_holes(faces, edges)) == 1
    assert detect_bosses_full(faces, edges) == []
    assert detect_cavities_full(faces, edges) == []


def test_boss_shape_has_no_holes_or_cavities():
    plate = Box(50, 50, 10)
    boss = Pos(0, 0, 5 + 15 / 2) * Cylinder(radius=8, height=15)
    shape = plate + boss
    faces, edges = _faces_and_edges(shape)
    assert detect_holes(faces, edges) == []
    assert len(detect_bosses_full(faces, edges)) == 1
    assert detect_cavities_full(faces, edges) == []