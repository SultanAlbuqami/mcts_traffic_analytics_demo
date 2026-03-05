# Saudi Compliance Reference

This file is intentionally high-level. It is meant to support project-level governance discussion, not replace legal or compliance review.

## Official reference points

### 1) Personal Data Protection Law (PDPL)

Official SDAIA National Data Governance Platform pages state that:

- the PDPL was issued by Royal Decree No. `M/19` dated `09/02/1443 AH`
- it was amended by Royal Decree No. `M/148` dated `05/09/1444 AH`
- the platform provides tools, guides, and advisory services to help entities comply with the PDPL and its Implementing Regulations

Official references:

- https://dgp.sdaia.gov.sa/wps/portal/pdp/about
- https://dgp.sdaia.gov.sa/wps/portal/pdp/knowledgecenter/details/PDPLCP

### 2) National Data Governance Platform

The official platform describes itself as a national electronic platform for data management and governance, personal data protection, compliance assessment, complaints, and guidance.

Official references:

- https://dgp.sdaia.gov.sa/
- https://dgp.sdaia.gov.sa/wps/portal/pdp/about/objectives

### 3) National Data Bank / Data Lake / Data Marketplace

The official National Data Bank site describes national platforms intended to improve data quality, enhance sharing between entities, and support data-driven decisions. It also describes the Data Lake and Data Marketplace as mechanisms for national-scale data integration and governed sharing.

Official references:

- https://data.gov.sa/en
- https://lake.data.gov.sa/en
- https://lake.data.gov.sa/en/services/data-integration-request
- https://api.data.gov.sa/

## How to position this project

You can say:

- "This project is a demo that aligns conceptually with Saudi requirements for governed data use, traceability, quality, and controlled sharing."
- "I am not claiming this is a legal compliance product; I am showing the architecture and controls I would expect before production deployment."
- "For real deployment, I would map the solution to organizational policies and the relevant SDAIA / NDMO controls with legal and governance teams."

## Practical alignment shown in this demo

- Traceability fields on ingested records
- Quality checks before reporting
- Documentation of assumptions and limitations
- Separation of raw, processed, and BI delivery layers
- Explicit notes on privacy, access control concepts, and governed sharing

## Institutional alignment note: Ministerial Committee for Traffic Safety

In practical delivery terms, this demo can support committee-style responsibilities such as:

- strategy monitoring through KPI trends and intervention scenarios
- cross-entity coordination using common definitions, lineage, and quality gates
- periodic reporting packs for senior economic/development governance forums
- public safety culture support through clear, explainable insight narratives

This remains a technical demonstration and does not replace formal institutional governance workflows.
