# Security

## Reporting a vulnerability

Please **do not open a public issue**. Report privately through
[GitHub Security Advisories](https://github.com/NvkAnirudh/recollect/security/advisories/new).
You'll get an acknowledgement within 72 hours.

## If a secret is committed

This repository is public, so treat any committed secret as compromised, even if the
commit is reverted straight away.

1. **Rotate it first** (Supabase, Gemini, Bright Data, Slack, Railway…), then remove it from the code.
2. Check the provider's logs for use of the leaked credential.
3. Note it in the PR or issue that fixes it.

## Baseline

The controls in place, from pre-commit hooks to runtime protections, are listed in
[ADR 0004](docs/adr/0004-public-repo-security-baseline.md).

Known gap: the web app's Content-Security-Policy does not yet restrict scripts (needs nonce-based
CSP with dynamic rendering). It is tracked as a follow-up.
