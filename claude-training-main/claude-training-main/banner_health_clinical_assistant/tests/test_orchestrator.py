from ehr_mock import EHRSystemMock
from llm_client import ClaudeClient
from models import EncounterStatus, GeneratedBy
from orchestrator import EncounterPipeline
from sample_data import create_sample_encounters


def make_pipeline():
    # Force mock mode so tests never hit the network.
    return EncounterPipeline(ehr_client=EHRSystemMock(), llm_client=ClaudeClient(force_mock=True))


def test_full_pipeline_end_to_end():
    scenario = create_sample_encounters()[0]
    pipeline = make_pipeline()

    encounter = pipeline.start_encounter(scenario.patient_id, scenario.provider_id)
    assert encounter.status == EncounterStatus.IN_PROGRESS

    segments = pipeline.ingest_transcript(encounter, scenario.raw_dictation_text)
    assert encounter.status == EncounterStatus.TRANSCRIBED
    assert len(segments) > 0

    history_summary = pipeline.fetch_history(encounter)
    assert history_summary and "Patient:" in history_summary

    draft = pipeline.generate_draft(encounter, segments, history_summary)
    assert encounter.status == EncounterStatus.DRAFTED
    assert draft.generated_by == GeneratedBy.MOCK

    edited_sections = dict(draft.sections)
    edited_sections["plan"] = "Follow up in two weeks."
    review = pipeline.submit_review(encounter, draft, edited_sections, reviewer_id=scenario.provider_id)
    assert encounter.status == EncounterStatus.REVIEWED
    assert review.approved is False

    document_id = pipeline.sign_and_deliver(encounter, review)
    assert encounter.status == EncounterStatus.SIGNED
    assert document_id.startswith("doc-")
    assert review.approved is True

    events = pipeline.audit_agent.events_for(encounter.id)
    event_types = [e.event_type for e in events]
    assert event_types == [
        "encounter_started",
        "transcript_ingested",
        "history_fetched",
        "draft_generated",
        "review_submitted",
        "note_signed_and_delivered",
    ]
