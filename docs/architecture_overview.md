# Architecture Overview

```mermaid
flowchart LR
    A[Raw Sources\nroads / accidents / violations / sensors / weather]
    B[Ingest Layer\ntraceability + batch lineage]
    C[Transform Layer\ncleaning + enrichment + road-day modeling table]
    D[Quality Layer\nschema / keys / ranges / coverage]
    E[Analytics Layer\nexecutive KPIs + diagnostics]
    F[Model Layer\ntemporal validation + group checks]
    G[Delivery Layer\nMarkdown reports + Streamlit + Power BI export]

    A --> B --> C --> D
    C --> E
    C --> F
    D --> G
    E --> G
    F --> G
```

## Explanation

- Raw sources stay separated to demonstrate multi-source collection.
- Ingest adds lineage fields for traceability.
- Transform enriches events and produces a reusable `road-day` analytical grain.
- Quality gates validate the data before reporting.
- Analytics and predictive outputs are delivered to leadership through reports, dashboard views, and a Power BI-ready star schema.
