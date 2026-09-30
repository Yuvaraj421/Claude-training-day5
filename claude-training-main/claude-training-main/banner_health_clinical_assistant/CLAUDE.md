# CLAUDE.md — Banner Health Clinical Assistant

Dev context for working on this project. See [`README.md`](README.md) for setup/run
instructions and [`../claude_in_healthcare/01-banner-health-clinical-documentation.md`](../claude_in_healthcare/01-banner-health-clinical-documentation.md)
for the design doc this implements.

## Architecture map

`main.py` (Streamlit UI) → `orchestrator.EncounterPipeline` → agents in `agents/`.

Each agent has exactly one responsibility and takes/returns the dataclasses in
`models.py`. The orchestrator is the only place that sequences them — agents
never call each other directly.

| Agent | File | Responsibility |
|---|---|---|
| `TranscriptionAgent` | `agents/transcription_agent.py` | Simulated ASR: dictation text → `TranscriptSegment` list |
| `EHRHistoryAgent` | `agents/ehr_history_agent.py` | Fetch + condense mock patient history |
| `DraftingAgent` | `agents/drafting_agent.py` | Call `llm_client.ClaudeClient` to produce a `ClinicalNoteDraft` |
| `ReviewAgent` | `agents/review_agent.py` | Diff clinician edits vs. AI draft, sign-off |
| `AuditAgent` | `agents/audit_agent.py` | Append-only event log per encounter |

`ehr_mock.EHRSystemMock` and `llm_client.ClaudeClient` are the two external-system
boundaries — everything else is pure Python with no I/O, which is why they're
injected into `EncounterPipeline.__init__` (see `tests/test_orchestrator.py` for
how tests force mock mode by passing `ClaudeClient(api_key=None)`).

## Adding a new pipeline step

1. Add a new agent class in `agents/` subclassing `BaseAgent`, with one public method.
2. Export it from `agents/__init__.py`.
3. Wire it into `EncounterPipeline` in `orchestrator.py`, adding an `audit_agent.log(...)` call for the new step.
4. Add a step to the `main.py` UI flow (each step is gated behind `st.session_state` so Streamlit reruns don't repeat work).
5. Add a unit test in `tests/test_agents.py` and update the end-to-end assertion in `tests/test_orchestrator.py`.

## Testing

```bash
pytest tests/
```

Tests never call the real Anthropic API — always construct `ClaudeClient(api_key=None)`
(or omit `ANTHROPIC_API_KEY` from the environment) so `DraftingAgent` falls back to
the deterministic mock generator.

## Notes

- `models.py` dataclasses intentionally mirror the design doc's section 3.2 data models field-for-field.
- `llm_client.ClaudeClient._parse_sections` expects the LLM to return a JSON object with
  `subjective`/`objective`/`assessment`/`plan` keys (enforced via the system prompt); if the
  model ever returns malformed JSON, the API call will raise and `generate_note` falls back to mock.
