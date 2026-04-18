# Contributing to MirrorMatch

Thanks for considering a contribution. MirrorMatch is MIT-licensed and welcomes issues, discussion, and pull requests.

## Ground rules

- Adhere to [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Open an issue before large changes so we can align on scope.
- Keep PRs focused: one concern per PR.
- Include tests. Backend diff/adapter changes must maintain ≥85% coverage.
- Update documentation for user-visible changes.

## Dev setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest            # run tests
ruff check .      # lint
mypy src          # types
```

### Frontend

```bash
cd frontend
pnpm install
pnpm test
pnpm lint
pnpm build
```

## Commit / PR style

- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- PR description: what + why; screenshots for UI changes; link to issue.

## Reporting bugs

Include: reproduction steps, expected vs actual, MirrorMatch version, OS/Python/Node versions.

## Security

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).

## Releases

1. Bump `backend/src/mirror_match/__init__.py`, `backend/pyproject.toml`, and
   `frontend/package.json` to the new version.
2. Add a `## [X.Y.Z] — YYYY-MM-DD` section to [CHANGELOG.md](CHANGELOG.md).
3. `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. The `release.yml` workflow builds multi-arch Docker images for both
   services and publishes them to
   `ghcr.io/<owner>/mirror-match-{backend,frontend}:{X.Y.Z,latest}`.
