# Analytics Standards and Templates

This document defines minimal internal standards to demonstrate analytics maturity.

## 1) KPI Definition Standard

Each KPI should include:

1. Name and owner
2. Business intent
3. Formula and grain
4. Data sources
5. Refresh cadence
6. Thresholds and alert logic
7. Limitations and caveats

## 2) Data Contract Standard (per source)

1. Source system name and owner
2. Expected schema
3. Required keys
4. Refresh SLA
5. Quality rules (null, duplicates, ranges, referential integrity)
6. Escalation path for data issues

## 3) Model Documentation Standard

1. Target definition
2. Features and exclusions
3. Split strategy and validation setup
4. Metrics (AUC/F1/Precision/Recall) and thresholds
5. Group-level checks and known limitations
6. Usage constraints (decision support only)

## 4) Executive Report Standard

1. Decision-ready summary (what decision should be made)
2. KPI trend and variance explanation
3. Top risks and affected entities
4. Recommended actions with expected impact
5. Assumptions and limitations

## 5) Review Checklist (Release Gate)

1. Quality gate is PASS/WARN with explained risks
2. Traceability fields present for required datasets
3. Model report generated and reviewed
4. Scenario analysis generated
5. Stakeholder pack generated
6. Governance notes updated for scope changes
