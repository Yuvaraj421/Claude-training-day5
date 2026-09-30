# Claude in Healthcare — Case Study Design Docs

Technical design documentation (High-Level Design + Low-Level Design) for a sample of published healthcare & life-sciences AI deployments. Each doc reconstructs a plausible architecture based on common patterns for the class of system described — see the disclaimer at the top of each file.

| # | Case Study | Reported Outcome | Doc |
|---|---|---|---|
| 1 | Banner Health | AI clinical assistant drafts documentation & summarizes records to reduce physician burnout | [01-banner-health-clinical-documentation.md](01-banner-health-clinical-documentation.md) |
| 2 | Qualified Health | Screens fragmented records at population scale to identify candidates for life-saving treatments | [02-qualified-health-patient-screening.md](02-qualified-health-patient-screening.md) |
| 3 | Carta Healthcare | 66% faster clinical data extraction/structuring at ~99% accuracy | [03-carta-healthcare-clinical-data-processing.md](03-carta-healthcare-clinical-data-processing.md) |
| 4 | Elation Health | Primary-care EHR platform — 61% less time on chart review | [04-elation-health-chart-review.md](04-elation-health-chart-review.md) |
| 5 | Commure | Clinical documentation automation at multi-tenant scale, saving millions of clinician hours | [05-commure-clinical-documentation-automation.md](05-commure-clinical-documentation-automation.md) |

Each doc follows the same structure:
1. **Overview** — vendor, problem, reported outcome, users
2. **HLD** — system context diagram (Mermaid), component table, non-functional requirements
3. **LLD** — data flow (sequence diagram), data models, API surface, tech stack, key processing steps
