# FaberAI Frontend

React + TypeScript frontend for FaberAI, built with [Vite](https://vitejs.dev/).

## Prerequisites

- Node.js 20+
- npm

## Install

```
cd frontend
npm install
```

This also sets up the pre-commit hook (via husky) that lints and formats staged files.

## Configure environment

```
cp .env.example .env
```

Fill in `VITE_API_BASE_URL` with the backend's local address (see `backend/`). The Supabase
values are placeholders for future auth work and are not required for local development yet.

## Run

```
npm run dev
```

Starts the Vite dev server (default: http://localhost:5173).

## Other scripts

| Command                | Description                              |
| ---------------------- | ---------------------------------------- |
| `npm run build`        | Type-check and build for production      |
| `npm run preview`      | Preview the production build locally     |
| `npm run lint`         | Run ESLint                               |
| `npm run format`       | Format files with Prettier               |
| `npm run format:check` | Check formatting without writing changes |

## Conventions

See [CONTRIBUTING.md](../CONTRIBUTING.md) at the repo root for branch naming and PR conventions.
