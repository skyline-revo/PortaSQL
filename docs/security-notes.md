# Security Notes

## What Was Removed or Limited in the Public Version

- Production/internal configuration files
- Any local credentials and deployment secrets
- Private endpoints and infrastructure references
- Private datasets and generated production DB artifacts
- Full internal retrieval/ranking logic considered proprietary

## Why These Pieces Are Not Public

This repository is intended for portfolio evaluation. Publicly exposing all operational and proprietary internals is not appropriate from security and IP perspectives.

## Secrets Handling Guidance (Real Usage)

- Keep secrets in environment variables, not source code.
- Do not commit `.env` or credential files.
- Rotate API keys regularly.
- Use least-privilege credentials per environment.
- Maintain separate configs for local/dev/prod.

## Public Repo Safety Practices Used Here

- `.gitignore` blocks virtualenvs, DB artifacts, caches, and local env files.
- `.env.example` provides placeholders only.
- `config/config.example.yaml` uses fake/demo-safe values.
- Public demo connector uses local sample data.
