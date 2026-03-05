# Contributing Guide

Thank you for your interest in contributing to the MCTS Traffic Analytics Demo.  
This is a portfolio project demonstrating governed, enterprise-grade analytics engineering.

## Ground Rules

1. **No real data** — all data must remain synthetic. Never add real traffic records, personal data, or government data.
2. **Offline-first** — all features must work without external API keys or cloud services.
3. **Deterministic** — use `seed=42` for any synthetic data generation.
4. **Minimal scope** — targeted, focused changes. No large refactors unless required.

## Getting Started

```bash
# 1. Fork and clone the repository
git clone https://github.com/SultanAlbuqami/mcts_traffic_analytics_demo.git
cd mcts-traffic-analytics-demo

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install runtime + dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# 4. Verify baseline
python -m pytest -q
python -m ruff check .
python -m ruff format . --check
```

## Pull Request Checklist

Before opening a PR, ensure:

- [ ] `python -m pytest -q` passes (all tests green)
- [ ] `python -m ruff check .` passes (no lint errors)
- [ ] `python -m ruff format . --check` passes (code is formatted)
- [ ] New behavior is covered by at least one test
- [ ] No secrets, keys, or real data added
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Bug fix | `fix/<short-description>` | `fix/sensor-null-handling` |
| Feature | `feat/<short-description>` | `feat/new-kpi-metric` |
| Docs | `docs/<what>` | `docs/powerbi-guide` |
| Chore | `chore/<what>` | `chore/dependency-update` |

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add violation trend chart to dashboard
fix: handle missing weather data in sensor join
docs: update Power BI setup steps
chore: bump ruff to 0.4.0
```

## Code Style

- Formatter: **ruff** (configured in `pyproject.toml`)
- Linter: **ruff** 
- Type hints encouraged but not strictly enforced (mypy optional)
- Follow existing patterns in `src/traffic_analytics_demo/`

## Adding Tests

- Unit tests: `tests/test_<module>.py`
- Use `tmp_path` (pytest fixture) for file I/O tests
- Mock external calls (LLM, network) — no live API dependencies in tests
- Keep tests fast: full pipeline integration tests use `--days 30` smoke size

## Reporting Issues

Use [GitHub Issues](https://github.com/SultanAlbuqami/mcts_traffic_analytics_demo/issues).  
For security issues, see [SECURITY.md](SECURITY.md).
