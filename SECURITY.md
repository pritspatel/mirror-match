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

MirrorMatch persists the `CompareRequest` to the job store so jobs can be
replayed via permalinks. Before writing, the request is scrubbed:

- HTTP / ES auth fields (`token`, `api_key`, `username`, `password`) are
  replaced with `***REDACTED***`.
- Sensitive header names (`Authorization`, `Proxy-Authorization`, `Cookie`,
  `X-API-Key`, case-insensitive) are redacted.

The raw secret is still used for the live `fetch` call — only the persisted
copy is scrubbed. Logs never include secrets.

Still, treat the job-store file as sensitive: it contains source URLs, host
names, and any non-redacted header a user adds. If you use custom header names
for auth, open an issue or extend `_SENSITIVE_HEADER_NAMES` in
`backend/src/mirror_match/api/redact.py`.
