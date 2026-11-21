# Contributing to FaberAI

Start with the root [quick start](README.md#run-locally). Use the
[backend guide](backend/README.md) for Python development and the
[frontend guide](frontend/README.md) for Vite hot reload. The
[architecture guide](ARCHITECTURE.md) describes service responsibilities.

## Branches and pull requests

- Use `feat/short-description` for features and `fix/short-description` for fixes
  or maintenance work.
- Open a PR into `main` and fill out the repository PR template.
- Describe the resulting behavior and relevant validation. Request review and
  satisfy the repository's required checks and approvals before merging.
- Delete the feature branch after merging.

## Validation

With `backend/requirements-dev.txt` installed, run from the repository root:

```sh
python -m ruff check backend scripts
python -m pytest backend/tests -q
```

From `frontend/`, run:

```sh
npm ci
npm run lint
npm run format:check
npm run build
```

Git attributes use LF for source and documentation on all platforms. If an older
Windows checkout still contains CRLF frontend files, `npm run format` normalizes
them. Review `git diff` before committing; formatting should not change behavior.

When changing uploads, geometry, storage, reports, or Docker setup, also verify
the running stack from the repository root:

```sh
docker compose up --build --detach --wait --wait-timeout 240
python scripts/smoke_test.py
python scripts/smoke_test.py --file path/to/a/test-part.step
```

The smoke test accepts `--api-url` and `--web-url` when using custom ports. These
commands create local analysis records; use test parts. Live AI benchmarks are
optional and require explicit provider credentials; see the
[benchmark guide](backend/tests/ai_eval/README.md).

## Dependency and documentation changes

- Keep direct runtime dependencies in `backend/requirements-runtime.txt`.
  Development and knowledge requirements include it rather than copying pins.
- Backend CI uses the development group; optional embedding and tracing packages
  belong in the knowledge group. `backend/requirements.txt` installs both groups.
- Use `npm ci` for a locked frontend install. Commit `frontend/package-lock.json`
  when intentionally changing frontend dependencies.
- Update setup instructions and the architecture/API guides when changing their
  behavior. Keep real credentials and generated data out of commits.
