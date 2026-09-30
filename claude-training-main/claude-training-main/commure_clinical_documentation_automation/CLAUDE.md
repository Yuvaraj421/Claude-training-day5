# CLAUDE.md — Commure Clinical Documentation Automation

Dev context for working on this project. See [`README.md`](README.md) for setup/run
instructions and [`../claude_in_healthcare/05-commure-clinical-documentation-automation.md`](../claude_in_healthcare/05-commure-clinical-documentation-automation.md)
for the design doc this implements.

## Architecture map

`main.py` (FastAPI API), `dashboard.py` (Streamlit UI), and `scripts/demo.py`
(console demo) each build their own `orchestrator.MultiTenantPipeline`, which
wires the agents in `agents/` onto a shared `streaming.EventBus`. They don't
share state — each entry point is a standalone in-memory demo.

Agents never call each other directly — only the bus. Each agent subscribes to
the topic it consumes in its own `__init__` and publishes the next topic itself:

| Agent | File | Subscribes to | Publishes |
|---|---|---|---|
| `IngestionAgent` | `agents/ingestion_agent.py` | — (entry point) | `encounter.audio` |
| `TranscriptionAgent` | `agents/transcription_agent.py` | `encounter.audio` | `transcript.ready` |
| `DocumentationAgent` | `agents/documentation_agent.py` | `transcript.ready` | `note.generated` |
| `DeliveryAgent` | `agents/delivery_agent.py` | `note.generated` | `encounter.completed` |
| `MonitoringAgent` | `agents/monitoring_agent.py` | all four topics | — (read-only observer) |

Because `EventBus.publish` dispatches synchronously and recursively, a single
call to `IngestionAgent.capture()` (or a publish onto `encounter.audio`) runs
the entire pipeline — including EHR delivery — before it returns. That's the
demo's stand-in for what would be an async, horizontally-scaled flow in
production; don't add real threading/async here, it would just obscure the
sequencing without changing what the demo teaches.

`tenant_store.TenantConfigService`, `encounter_store.EncounterStore`, and
`ehr_adapters.EHRAdapterRegistry` are the shared, tenant-aware state every
agent reads/writes through — never keep tenant state inside an agent itself.

## Multi-tenancy rules

- Every model in `models.py` carries a `tenant_id`. Every `EncounterStore`
  read method takes `tenant_id` as its first argument and raises
  `TenantIsolationError` (not just an empty result) if the record belongs to
  a different tenant — see `tests/test_tenant_isolation.py`.
- `DocumentationAgent` always resolves the tenant's `NoteTemplate` for the
  encounter's specialty before calling the LLM — never hardcode a section
  schema in an agent or in `llm_client.py`.
- `DeliveryAgent` always routes through `EHRAdapterRegistry.get(tenant.ehr_vendor)`
  — never call a specific vendor adapter class directly from pipeline code.

## Adding a new EHR vendor

1. Add `EHRVendor.<VENDOR>` to `models.py`.
2. Add `ehr_adapters/<vendor>_adapter.py` subclassing `EHRAdapter` (see
   `ehr_adapters/base.py`), returning a vendor-prefixed document ID.
3. Register it in `EHRAdapterRegistry.__init__` (`ehr_adapters/registry.py`).
4. Export it from `ehr_adapters/__init__.py`.
5. Add a test in `tests/test_agents.py` asserting the document ID prefix for
   a tenant configured with that vendor.

## Adding a new pipeline stage

1. Add a new agent class in `agents/` subclassing `BaseAgent`, subscribing to
   whatever topic it consumes in `__init__` and publishing its own topic.
2. Export it from `agents/__init__.py`.
3. Instantiate it in `MultiTenantPipeline.__init__` (`orchestrator.py`).
4. Add a unit test in `tests/test_agents.py` and update the end-to-end
   assertions in `tests/test_orchestrator.py`.

## Testing

```bash
pytest tests/
```

Tests never call the real Anthropic API — always construct
`ClaudeClient(force_mock=True)` (or omit `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN`
from the environment) so `DocumentationAgent` falls back to the deterministic
mock generator. `tests/test_api.py` rebuilds `main.pipeline` per-test (via the
`client` fixture) since it's a module-level global — don't remove that reset or
tests will leak state across each other.

## Notes

- `models.py` dataclasses intentionally mirror the design doc's section 3.2
  data models field-for-field.
- `main.py`'s two-step `/encounters` then `/encounters/{id}/audio` matches the
  doc's API surface (register, then upload audio separately); the audio
  endpoint publishes onto `encounter.audio` rather than calling
  `TranscriptionAgent` directly, so it exercises the same bus path as
  `orchestrator.submit_encounter` / `IngestionAgent.capture`.
- The `/deliver` endpoint is idempotent by design: in this synchronous demo,
  delivery already happens automatically once `DocumentationAgent` publishes
  `note.generated`, so `/deliver` just returns the existing result unless the
  note somehow hasn't been delivered yet.
- `dashboard.py` uses `orchestrator.submit_encounter()` directly (not the bus
  publish pattern `main.py`'s `/audio` endpoint uses) since it always has a
  freshly-created encounter with no audio yet — same effect, just entering
  through `IngestionAgent.capture()` instead of a raw `bus.publish`.
- `dashboard.py`'s categorical bar colors (`CATEGORICAL` list) and status colors
  come from the dataviz skill's validated default palette — if you add a chart,
  reuse those constants rather than picking new hex values, and keep each
  measure (e.g. "delivered count" vs "latency ms") in its own chart per the
  one-axis rule rather than combining them into a dual-axis chart.
- `assistant.PlatformAssistant` is a separate concern from `llm_client.ClaudeClient`:
  the latter drafts notes from a fixed system prompt, the former is a tool-calling
  chat loop over `orchestrator.MultiTenantPipeline` (list/register tenants, set
  templates, submit encounters, read metrics/notes — see `TOOLS` and `TOOL_HANDLERS`
  in `assistant.py`, one function per tool). Both resolve their live/mock Anthropic
  client via the shared `anthropic_client.resolve_client()` (`ANTHROPIC_API_KEY`/
  `ANTHROPIC_AUTH_TOKEN`, or `force_mock=True` in tests) — add any new Anthropic-backed
  component through that helper rather than re-deriving credential resolution.
  `PlatformAssistant`'s mock fallback is a small keyword command parser, not a
  templated generator, since free-form chat has no deterministic equivalent.
  When storing multi-turn tool-use history (e.g. in `st.session_state`), always
  convert SDK response content blocks to plain dicts via `block.model_dump()` before
  appending — keeping the raw SDK objects around across a Streamlit rerun boundary
  can trip a `pydantic`/`typing.Union` validation error. Note this can still surface
  as a flaky, harmless-in-practice error under `streamlit.testing.v1.AppTest`'s bare
  script-rerun mode after several `.run()` calls in one test process — `PlatformAssistant.respond`
  already catches it and falls back to mock mode, so treat it as a test-harness quirk,
  not evidence of a real bug, unless it reproduces against the actual running app.
- Tenant lookup by human-typed name (fuzzy, case-insensitive substring match, only
  when unambiguous) lives on `TenantConfigService.find_tenant` — reuse it rather than
  re-deriving name matching in a new caller; `dashboard.py`'s tenant selectboxes use
  the exact-match `select_tenant()` helper instead since there the user always picks
  from a rendered list, not a typed name.
