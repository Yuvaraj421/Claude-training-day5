# Banner Health Clinical Assistant (Demo)

An educational, runnable implementation of the **Banner Health — Reducing Physician
Burnout at Scale** case study design ([`claude_in_healthcare/01-banner-health-clinical-documentation.md`](../claude_in_healthcare/01-banner-health-clinical-documentation.md)):
an AI clinical assistant that drafts documentation and summarizes patient records
so physicians spend less time on paperwork.

> **Disclaimer:** This is an illustrative build for architectural learning, not
> Banner Health's real system. All patients, transcripts, and EHR data in this
> demo are synthetic.

## What it does

Walks through the encounter-to-signed-note flow from the design doc:

```
Clinician dictation → simulated ASR → EHR history lookup → AI-drafted SOAP note
  → clinician review/edit → sign-off → push to EHR (mock) → audit trail
```

Each pipeline stage is a single-responsibility **agent** (`agents/`), wired together
by `orchestrator.py` in the same order as the design doc's sequence diagram.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY (optional)
```

Without an `ANTHROPIC_API_KEY`, the app runs in **mock mode**: drafting uses a
deterministic templated note generator instead of a live Claude call, so the
whole demo still works offline.

## Run

```bash
streamlit run main.py
```

Pick a sample encounter in the sidebar, then step through: start encounter →
fetch history → generate AI draft → edit sections → approve & sign. The signed
note, diff vs. the AI draft, and full audit trail are shown at the end.

## Run tests

```bash
pytest tests/
```

Tests force mock mode, so they run with no network access and no API key.

## Architecture

```
agents/
  transcription_agent.py   simulated ASR: raw dictation text -> transcript segments
  ehr_history_agent.py     pulls & condenses mock patient history from the EHR
  drafting_agent.py        calls the LLM (or mock) to draft a structured SOAP note
  review_agent.py          clinician edit diffing + sign-off
  audit_agent.py           append-only audit trail (AI-generated vs. human-edited)
models.py                  Encounter, TranscriptSegment, ClinicalNoteDraft, NoteReview
ehr_mock.py                in-memory mock EHR (patient lookup + signed-note write-back)
llm_client.py              Anthropic API wrapper with mock fallback
orchestrator.py            EncounterPipeline — runs the agents in sequence
sample_data.py             synthetic sample encounter scenarios
main.py                    Streamlit UI
```

See [`CLAUDE.md`](CLAUDE.md) for how to extend the pipeline.
