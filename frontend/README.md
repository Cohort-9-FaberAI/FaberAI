# FaberAI frontend

React, TypeScript, Vite, Three.js, and Zustand power the primary web interface.
For the complete Docker application, see the root
[quick start](../README.md#run-locally). The steps below enable Vite hot reload.

## Development

Use Node.js 22+ and npm. From the repository root, start the backend services:

```sh
docker compose up --build --detach --wait --wait-timeout 240 api
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. If the containerized frontend already owns that port,
stop it with `docker compose stop frontend` from the repository root first.
`npm ci` also installs the Husky hook, which lints and formats staged frontend files.

## Configuration

The API address defaults to `http://127.0.0.1:8000`. To override it, copy
`.env.example` to `.env` in this directory and set `VITE_API_BASE_URL`. On
PowerShell, use `Copy-Item .env.example .env`. Restart Vite after changing it.

The current sign-in stores a local demo identity; it does not authenticate an
account. The Supabase variables in the example are reserved for future auth
integration and are not needed for development. Backend storage is configured
separately in the [backend guide](../backend/README.md).

## Source map

| Location                      | Responsibility                                               |
| ----------------------------- | ------------------------------------------------------------ |
| `pages/`                      | Route-level screens                                          |
| `components/workspace/steps/` | Setup, inspection, verdict, and export                       |
| `hooks/useFileWorkspace.ts`   | Shared file-scoped settings, analysis, and preview selection |
| `components/ModelPreview/`    | CAD rendering, issue markers, and viewer controls            |
| `components/export/`          | Inline PDF report preview                                    |
| `lib/api.ts`                  | Typed API requests and PDF downloads                         |
| `lib/useTaskPolling.ts`       | Background task status polling                               |
| `lib/analysisView.ts`         | Report scores, process filtering, and issue display helpers  |
| `store/`                      | Zustand project, workspace, theme, and interaction state     |

Paths in this table are relative to `src/`. The `/debug` route provides a manual
API inspection screen. Legacy route names redirect to the current workspace.

## Checks and builds

| Command                | Purpose                                |
| ---------------------- | -------------------------------------- |
| `npm run lint`         | ESLint checks                          |
| `npm run format:check` | Prettier check without writing         |
| `npm run format`       | Apply formatting                       |
| `npm run build`        | Type-check and build production assets |
| `npm run preview`      | Serve the production build locally     |

Git attributes normalize source files to LF across Windows and Linux checkouts.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for repository checks and PR conventions.
