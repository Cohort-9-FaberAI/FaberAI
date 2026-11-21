# Notebooks

This directory is reserved for exploratory data science and CAD notebooks. It
is not imported by the API or worker, and no notebooks are currently checked in.
Use the optional [Conda environment](../README-DS.md) for experiments, or the
[backend development environment](../README.md) for reusable Python code.

Move reusable geometry logic into `backend/geometry/` and add focused checks in
`backend/tests/geometry/`. Keep datasets and generated outputs out of commits
unless they are intentionally small, documented test fixtures.
