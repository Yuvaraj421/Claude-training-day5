# Commure Clinical Documentation Automation (Demo)

An educational, runnable implementation of the **Commure — Clinical Documentation
Automation at Scale** case study design
([`claude_in_healthcare/05-commure-clinical-documentation-automation.md`](../claude_in_healthcare/05-commure-clinical-documentation-automation.md)):
a multi-tenant ambient clinical documentation platform that turns encounter audio
into structured notes and pushes them into each health system's own EHR.

> **Disclaimer:** This is an illustrative build for architectural learning, not
> Commure's real system. All tenants, clinicians, transcripts, and EHR payloads
> in this demo are synthetic.

## What it does

Walks through the multi-tenant encounter flow from the design doc's sequence
diagram (section 3.1):

```
Ambient capture (tenant-tagged) → edge ingestion → streaming backbone → ASR
  → streaming backbone → LLM documentation (tenant template resolved)
  → EHR adapter (per-vendor) → tenant's EHR → completion event → monitoring
```

The distinguishing challenge modeled here vs. a single-health-system deployment
is **multi-tenant scale**: every record carries a `tenant_id`, one shared LLM
pool serves per-tenant note templates/specialties, and a per-vendor adapter
layer routes delivery to each tenant's actual EHR (Epic, Cerner, athenahealth).

Each pipeline stage is a single-responsibility **agent** (`agents/`) that only
talks to the rest of the pipeline by publishing/consuming events on an
in-process `EventBus` (`streaming.py`) — standing in for the Kafka-style
streaming backbone in the design doc. The one LLM-backed agent is
`DocumentationAgent`, which resolves each tenant's `NoteTemplate` before
calling Claude.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY (optional)
```

Without an `ANTHROPIC_API_KEY`, the app runs in **mock mode**: documentation
generation uses a deterministic templated note generator instead of a live
Claude call, so the whole demo still works offline.

## Run

**Dashboard (recommended)** — a platform-operator UI over the same pipeline,
no server to stand up separately:

```bash
streamlit run dashboard.py
```

Comes pre-seeded with three tenants (Epic/Cerner/athenahealth). From there you can:
- **Submit Encounter** — pick a tenant, load a sample dictation (or write your own),
  submit it, and watch it move through capture → ASR → LLM drafting → EHR delivery,
  with the generated note sections and EHR document ID shown alongside a per-encounter
  event log.
- **Tenant Templates** — view/add per-specialty note templates for any tenant.
- **Platform Monitoring** — KPI tiles + per-tenant bar charts (encounters delivered,
  avg ASR latency) across all onboarded tenants.
- **Encounter History** — a table of every encounter across every tenant.
- **Assistant** — a chat tab (`assistant.PlatformAssistant`) that answers questions
  and takes actions over the same pipeline via Claude tool-calling ("metrics for
  Riverside?", "submit a cardiology encounter for Lakeshore saying..."). Falls back
  to a handful of recognized text commands (`list tenants`, `metrics for <tenant>`,
  `encounters for <tenant>`) in mock mode.
- Sidebar — live/mock mode indicator, and a form to onboard a new tenant on any
  supported EHR vendor.

**Console walkthrough** across the same three tenants, including a tenant-isolation
check:

```bash
python scripts/demo.py
```

**REST API** implementing the design doc's representative API surface (section 3.3):

```bash
uvicorn main:app --reload
```

Then, e.g.:

```bash
curl -X POST localhost:8000/v1/tenants \
  -H 'Content-Type: application/json' \
  -d '{"health_system_name": "Riverside Health Network", "ehr_vendor": "epic", "data_residency_region": "us-east"}'
```

Interactive docs at `http://localhost:8000/docs`.

The dashboard and the REST API each build their own `MultiTenantPipeline` in memory
(see `orchestrator.py`) — they don't share state, since this is a demo, not a real
deployment with a shared backing store.

## Run tests

```bash
pytest tests/
```

Tests force mock mode, so they run with no network access and no API key.

## Architecture

```
agents/
  ingestion_agent.py       ambient capture + edge ingestion: tags tenant_id, publishes encounter.audio
  transcription_agent.py   ASR Service Pool: encounter.audio -> Transcript -> transcript.ready
  documentation_agent.py   LLM Documentation Service Pool: resolves tenant template, calls Claude (or mock)
  delivery_agent.py        EHR Adapter Layer routing: note.generated -> tenant's EHR vendor adapter
  monitoring_agent.py      Scale/Quality Monitoring: per-tenant throughput/latency counters
ehr_adapters/
  epic_adapter.py          FHIR DocumentReference-shaped push
  cerner_adapter.py        Cerner proprietary note payload
  athenahealth_adapter.py  athenahealth REST/JSON document payload
  registry.py              routes a tenant's ehr_vendor -> adapter instance
models.py                  Tenant, Encounter, Transcript, NoteTemplate, GeneratedNote
tenant_store.py             Tenant Config & Template Service (in-memory)
encounter_store.py          Multi-Tenant Encounter Store, enforces tenant isolation on every read
streaming.py                in-process Event Streaming Backbone (pub/sub, stands in for Kafka)
anthropic_client.py           Shared live/mock Anthropic client resolution used by llm_client.py + assistant.py
llm_client.py                Anthropic API wrapper with per-tenant section schema + mock fallback
assistant.py                  Chat assistant over the pipeline (Claude tool-calling + mock command parser)
orchestrator.py              MultiTenantPipeline — wires agents onto the shared EventBus
sample_data.py                synthetic sample tenants + encounter scenarios
main.py                       FastAPI app implementing the design doc's API surface
dashboard.py                   Streamlit platform-operator UI (submit encounters, templates, monitoring, history)
scripts/demo.py                console walkthrough across tenants + isolation check
```

See [`CLAUDE.md`](CLAUDE.md) for how to extend the pipeline.
