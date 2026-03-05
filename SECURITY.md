# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security vulnerabilities privately via:

1. **GitHub private vulnerability reporting** (preferred):  
   Go to the repository → Security → "Report a vulnerability"

2. **Email** (fallback):  
   Contact the repository owner [@SultanAlbuqami](https://github.com/SultanAlbuqami) through GitHub's private messaging.

Include in your report:
- Description of the vulnerability and its potential impact
- Steps to reproduce (proof of concept if applicable)
- Affected version(s)
- Any suggested remediation

You will receive an acknowledgement within **5 business days** and a resolution timeline within **30 days** for confirmed issues.

## Scope

This project is a **portfolio / demo application** using fully **synthetic data**.  
No real personal data, traffic records, or government data is stored or processed.

**In-scope:**
- Dependency vulnerabilities (report via `pip-audit` findings)
- Dockerfile security weaknesses
- Authentication or authorization gaps if the project is deployed

**Out-of-scope:**
- Issues in demo data itself (it is intentionally synthetic)
- Rate-limiting or DoS on demo deployments (no production SLA)

## Security Defaults

- All data is synthetic (seed=42, no PII)
- Dockerfile runs as non-root user (`appuser`, UID 1001)
- No secrets are committed; use `.env.example` as a template
- LLM integration is opt-in and disabled by default (`TRAFFIC_ANALYTICS_LLM_PROVIDER=disabled`)

## Dependency Scanning

Run locally:
```bash
pip install pip-audit
pip-audit -r requirements.txt
```

CI runs `pip-audit` as an optional advisory step (non-blocking) to surface known CVEs.
