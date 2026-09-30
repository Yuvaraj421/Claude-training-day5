from agents.audit_agent import AuditAgent
from agents.drafting_agent import DraftingAgent
from agents.ehr_history_agent import EHRHistoryAgent
from agents.review_agent import ReviewAgent
from agents.transcription_agent import TranscriptionAgent
from ehr_mock import EHRSystemMock
from llm_client import ClaudeClient
from models import ClinicalNoteDraft, Encounter, GeneratedBy


def make_encounter():
    return Encounter(patient_id="pt-1001", provider_id="dr-chen")


def test_transcription_agent_splits_sentences_with_confidence():
    encounter = make_encounter()
    segments = TranscriptionAgent().transcribe(encounter, "First sentence. Second sentence!")

    assert [s.text for s in segments] == ["First sentence.", "Second sentence!"]
    assert all(0.0 <= s.confidence <= 1.0 for s in segments)
    assert [s.sequence for s in segments] == [0, 1]


def test_ehr_history_agent_returns_known_patient_summary():
    summary = EHRHistoryAgent().fetch_summary("pt-1001", EHRSystemMock())

    assert "Jordan Alvarez" in summary
    assert "Type 2 diabetes mellitus" in summary


def test_ehr_history_agent_handles_unknown_patient():
    summary = EHRHistoryAgent().fetch_summary("does-not-exist", EHRSystemMock())

    assert "No prior history" in summary


def test_drafting_agent_uses_mock_client_when_no_api_key():
    encounter = make_encounter()
    segments = TranscriptionAgent().transcribe(encounter, "Patient feels well today.")

    client = ClaudeClient(force_mock=True)
    draft = DraftingAgent(client).generate_draft(encounter, segments, "No prior history.")

    assert draft.generated_by == GeneratedBy.MOCK
    assert set(draft.sections.keys()) == {"subjective", "objective", "assessment", "plan"}


def test_review_agent_diff_is_empty_when_no_edits():
    draft = ClinicalNoteDraft(
        encounter_id="enc-1",
        sections={"subjective": "a", "objective": "b", "assessment": "c", "plan": "d"},
        generated_by=GeneratedBy.MOCK,
    )
    review = ReviewAgent().submit_review(draft, dict(draft.sections), "dr-chen")

    assert review.edits_diff == "No edits — signed as drafted."
    assert review.approved is False


def test_review_agent_diff_detects_changes_and_sign_sets_approved():
    draft = ClinicalNoteDraft(
        encounter_id="enc-1",
        sections={"subjective": "a", "objective": "b", "assessment": "c", "plan": "d"},
        generated_by=GeneratedBy.MOCK,
    )
    edited = dict(draft.sections)
    edited["plan"] = "changed plan"

    agent = ReviewAgent()
    review = agent.submit_review(draft, edited, "dr-chen")
    assert "changed plan" in review.edits_diff
    assert review.approved is False

    signed = agent.sign(review)
    assert signed.approved is True
    assert signed.signed_at is not None


def test_audit_agent_scopes_events_by_encounter():
    audit = AuditAgent()
    audit.log("enc-1", "event_a", "detail a")
    audit.log("enc-2", "event_b", "detail b")

    events = audit.events_for("enc-1")
    assert len(events) == 1
    assert events[0].event_type == "event_a"
