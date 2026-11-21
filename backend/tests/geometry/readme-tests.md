# Geometry tests

Install `backend/requirements-dev.txt` as described in the
[backend guide](../../README.md). From `backend/`, run:

```sh
python -m pytest tests/geometry -q
```

- `test_features.py` builds synthetic parts with build123d to check holes, bosses,
  and cavities without external fixture files.
- `test_measurements.py` checks geometry measurements; cases requiring optional
  pythonocc-core bindings skip when those bindings are unavailable.
- `test_step_optional.py` blocks optional CAD imports to verify clear STEP errors
  and continued STL support.

The broader suite also includes `tests/test_local_setup.py`, which exercises real
STL/STEP uploads, local persistence, preview generation, PDF export, and report
Q&A with queue transport replaced for offline testing. The Docker smoke workflow
checks those same service boundaries with a running Redis queue and worker.
