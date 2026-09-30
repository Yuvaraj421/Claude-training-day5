"""Banner Health Clinical Assistant — Streamlit demo.

Walks through the encounter-to-signed-note flow described in
claude_in_healthcare/01-banner-health-clinical-documentation.md:
capture -> ASR -> EHR history -> AI draft -> clinician review -> sign & deliver to EHR.

Educational demo only — not a real clinical system. All patient data is synthetic.
"""

import streamlit as st

from llm_client import ClaudeClient
from orchestrator import EncounterPipeline
from sample_data import create_sample_encounters

st.set_page_config(page_title="Banner Health Clinical Assistant", layout="wide")

if "pipeline" not in st.session_state:
    st.session_state.pipeline = EncounterPipeline()
if "encounter" not in st.session_state:
    st.session_state.encounter = None
    st.session_state.segments = None
    st.session_state.history_summary = None
    st.session_state.draft = None
    st.session_state.review = None
    st.session_state.document_id = None

pipeline: EncounterPipeline = st.session_state.pipeline

st.title("🩺 Banner Health Clinical Assistant")
st.caption(
    "Educational demo inspired by the published Banner Health case study "
    "(AI-assisted documentation to reduce physician burnout). Not a real clinical system."
)

if pipeline.drafting_agent.llm_client.is_live:
    st.success("Live mode: drafting with the Anthropic API (Claude).", icon="✅")
else:
    st.warning(
        "Mock mode: no ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN found — using a templated "
        "note generator instead of a live Claude call. Set one of those env vars to enable "
        "real AI drafting.",
        icon="⚠️",
    )

scenarios = create_sample_encounters()
scenario_labels = [s.label for s in scenarios]

with st.sidebar:
    st.header("1. Select encounter")
    chosen_label = st.selectbox("Sample encounter", scenario_labels)
    scenario = next(s for s in scenarios if s.label == chosen_label)

    if st.button("Start encounter", type="primary"):
        encounter = pipeline.start_encounter(scenario.patient_id, scenario.provider_id)
        segments = pipeline.ingest_transcript(encounter, scenario.raw_dictation_text)
        st.session_state.encounter = encounter
        st.session_state.segments = segments
        st.session_state.history_summary = None
        st.session_state.draft = None
        st.session_state.review = None
        st.session_state.document_id = None

encounter = st.session_state.encounter

if encounter is None:
    st.info("Choose a sample encounter and click **Start encounter** in the sidebar to begin.")
    st.stop()

st.subheader(f"Encounter `{encounter.id[:8]}` — status: {encounter.status.value}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📝 Simulated transcript (ASR output)")
    for seg in st.session_state.segments:
        st.markdown(f"- _{seg.text}_  &nbsp; `conf={seg.confidence}`")

with col2:
    st.markdown("### 📋 Patient history (from EHR)")
    if st.session_state.history_summary is None:
        if st.button("Fetch patient history"):
            st.session_state.history_summary = pipeline.fetch_history(encounter)
            st.rerun()
    else:
        st.text(st.session_state.history_summary)

if st.session_state.history_summary is None:
    st.stop()

st.markdown("---")
st.markdown("### 🤖 AI-drafted clinical note")

if st.session_state.draft is None:
    if st.button("Generate AI draft", type="primary"):
        st.session_state.draft = pipeline.generate_draft(
            encounter, st.session_state.segments, st.session_state.history_summary
        )
        st.rerun()
    st.stop()

draft = st.session_state.draft
if draft.generated_by.value == "mock":
    st.caption("⚠️ This draft was produced by the mock generator, not a live Claude call.")

st.markdown("#### Clinician review — edit any section before signing")
edited_sections = {}
for section in ("subjective", "objective", "assessment", "plan"):
    edited_sections[section] = st.text_area(
        section.capitalize(), value=draft.sections.get(section, ""), key=f"edit_{section}"
    )

reviewer_id = st.text_input("Reviewing clinician ID", value=encounter.provider_id)

if st.session_state.document_id is None:
    if st.button("Approve & sign", type="primary"):
        review = pipeline.submit_review(encounter, draft, edited_sections, reviewer_id)
        document_id = pipeline.sign_and_deliver(encounter, review)
        st.session_state.review = review
        st.session_state.document_id = document_id
        st.rerun()
else:
    st.success(f"Note signed and delivered to EHR. Document ID: `{st.session_state.document_id}`")

    st.markdown("#### Diff — AI draft vs. clinician-signed note")
    st.code(st.session_state.review.edits_diff or "No edits.", language="diff")

    st.markdown("#### Audit trail")
    for event in pipeline.audit_agent.events_for(encounter.id):
        st.text(f"[{event.timestamp.isoformat(timespec='seconds')}] {event.event_type}: {event.detail}")
