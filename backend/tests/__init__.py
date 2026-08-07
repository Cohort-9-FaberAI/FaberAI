"""Marks ``tests`` as a real package.

This file is load-bearing, not boilerplate. ``langtrace-python-sdk`` installs
its own top-level ``tests`` package into site-packages. Without an
``__init__.py`` here, ``backend/tests`` is only a namespace portion, and the
import machinery keeps scanning ``sys.path`` past it — so the regular package
in site-packages wins and ``from tests.ai_eval... import`` fails at collection
with ``ModuleNotFoundError: No module named 'tests.ai_eval'``.

The failure only appears where langtrace is installed (CI), so deleting this
file passes locally and breaks the pipeline.
"""
