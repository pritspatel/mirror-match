# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-18

### Added
- **Keyed-array diff**: `array_keys` option maps JSON-Pointer → field name so
  arrays are diffed by identity instead of position.
- **Numeric tolerance**: `numeric_tolerance` suppresses float diffs below an
  absolute delta. Bools are excluded from numeric matching.
- **Case-insensitive strings**: `case_insensitive` flag folds string values
  with `.casefold()` before equality.
- **SQLite job store**: every `/api/v1/compare*` call persists a `JobRecord`.
  DB path: `MIRROR_MATCH_DB_PATH` (default `mirror-match.db`).
- **Permalink routes**: `GET /api/v1/jobs/{id}`, `/jobs/{id}/csv`,
  `/jobs/{id}/html` replay any stored job.
- **Optional bearer auth**: set `MIRROR_MATCH_AUTH_TOKEN` to require
  `Authorization: Bearer <token>` on every route except `/healthz`, `/metrics`,
  and docs.
- **Prometheus `/metrics`**: request counters (bucketed by route) plus a
  summary of compare durations.
- **CLI**: `mirror-match compare a.json b.json [--csv|--html|--json] [--array-key POINTER=FIELD] [--numeric-tolerance N] [--case-insensitive]`.
- **Frontend**: Share-link button, hash-route replay (`#/jobs/<id>`), UI inputs
  for the three new compare options.
- **CI**: GitHub Actions runs ruff + pytest + coverage for backend and
  typecheck + build for frontend.
- Governance docs: `SECURITY.md`, `CHANGELOG.md`, issue + PR templates.

### Changed
- `/api/v1/compare` response now returns a persistent `job_id` that can be
  resolved via the permalink routes.

## [0.2.0] — 2026-04-18

### Added
- Elasticsearch and HTTP source adapters.
- Standalone HTML report (Jinja2 template, inline CSS, no CDN).
- Tree view for nested diffs, expand/collapse.
- MkDocs site.
- Integration-style adapter tests (respx for HTTP, fake ES client).

## [0.1.0] — 2026-04-18

### Added
- Initial MVP: raw JSON adapter, diff engine with JSON-Pointer paths,
  FastAPI `/api/v1/compare` endpoint, CSV export, React UI with Monaco
  editors, Docker Compose, MIT license.
