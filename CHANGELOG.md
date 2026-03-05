# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-03-05

### Added
- `LICENSE` — Apache-2.0 license
- `CHANGELOG.md` — this file (Keep a Changelog format)
- `SECURITY.md` — vulnerability reporting process and scope
- `CONTRIBUTING.md` — PR contribution guide and test standards
- `CODEOWNERS` — GitHub code ownership declaration
- `requirements-dev.txt` — separate dev/test dependency file
- `scripts/generate_data_dictionary.py` — auto-generates `docs/data_dictionary.md` from curated CSVs with sensitivity classification
- `docs/data_dictionary.md` — generated data dictionary for all curated tables
- `docs/story_one_pager.md` — problem → signal → decision → impact narrative
- `docs/assets/README.md` — instructions for safely capturing and adding screenshots
- `powerbi/README.md` — step-by-step Power BI model build guide
- `powerbi/tabular_editor/` — Tabular Editor TMSL and DAX scripts
- `.env.example` — annotated environment variable reference (no secrets)
- `tests/test_data_dictionary.py` — smoke test for dictionary generation

### Changed
- `README.md` — added "Demo in 5 Minutes" section, navigation table, architecture diagram, license/security/contributing links
- `pyproject.toml` — added `[tool.ruff]` configuration; bumped version to `0.1.1`; moved `pytest` out of runtime deps
- `requirements.txt` — removed `pytest` (moved to `requirements-dev.txt`)
- `Dockerfile` — added non-root `appuser`, explicit `HEALTHCHECK`, safe ENV defaults, copied data files for container runtime
- `.github/workflows/ci.yml` — added ruff lint + format check steps; split runtime vs dev installs

### Security
- Dockerfile now runs as non-root user `appuser` (UID 1001)
- `.env.example` replaces any temptation to commit secrets directly

## [0.1.0] - 2026-03-04

### Added
- Initial import: ETL pipeline, quality checks, predictive model, Streamlit dashboard, Power BI export, governed documentation, CI workflow, Dockerfile.

[Unreleased]: https://github.com/SultanAlbuqami/mcts_traffic_analytics_demo/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/SultanAlbuqami/mcts_traffic_analytics_demo/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/SultanAlbuqami/mcts_traffic_analytics_demo/releases/tag/v0.1.0
