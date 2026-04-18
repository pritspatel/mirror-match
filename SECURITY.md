# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |
| < 1.0   | ❌        |

## Reporting a Vulnerability

Do **not** open a public GitHub issue for security problems.

Instead, email the maintainers via GitHub Security Advisories:

1. Go to <https://github.com/pritspatel/mirror-match/security/advisories/new>
2. Describe the issue, reproduction steps, and impact.
3. You'll get an initial response within 5 business days.

If the issue is confirmed, we will coordinate a fix and a disclosure timeline
before publishing any patched release.

## Scope

In scope:

- Remote code execution in the backend
- Unauthenticated access to persisted diff jobs
- Secret leakage via logs, exports, or error messages
- XSS in the rendered HTML report
- CSRF against authenticated endpoints

Out of scope:

- Denial of service from intentionally huge inputs (enforce limits at your
  reverse proxy)
- Missing hardening in `examples/` or local dev setups
- Findings that require attacker-controlled environment variables or
  filesystem access

## Handling Secrets

MirrorMatch persists the full `CompareRequest` to the job store so jobs can be
replayed. If you submit credentials (HTTP bearer tokens, ES API keys) they
**will** be written to SQLite. Treat the DB file as sensitive and rotate any
credential that has appeared in a shared job.
