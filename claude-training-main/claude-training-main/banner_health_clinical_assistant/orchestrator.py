"""Encounter pipeline orchestrator.

Wires the agents in the exact order of the sequence diagram in
claude_in_healthcare/01-banner-health-clinical-documentation.md (section 3.1):
capture -> ASR -> EHR history -> LLM draft -> clinician review -> sign & push to EHR.
"""

from __future__ import annotations

from agents import AuditAgent, DraftingAgent, EHRHistoryAgent, ReviewAgent, TranscriptionAgent
from ehr_mock import EHRSystemMock
from llm_client import ClaudeClient
from models import ClinicalNoteDraft, Encounter, EncounterStatus, NoteReview, TranscriptSegment


class EncounterPipeline:
    def __init__(self, ehr_client: EHRSystemMock | None = None, llm_client: ClaudeClient | None = None):
        self.ehr_client = ehr_client or EHRSystemMock()
        self.transcription_agent = TranscriptionAgent()
        self.ehr_history_agent = EHRHistoryAgent()
        self.drafting_agent = DraftingAgent(llm_client or ClaudeClient())
        self.review_agent = ReviewAgent()
        self.audit_agent = AuditAgent()

    def start_encounter(self, patient_id: str, provider_id: str) -> Encounter:
        encounter = Encounter(patient_id=patient_id, provider_id=provider_id)
        self.audit_agent.log(encounter.id, "encounter_started", f"patient={patient_id} provider={provider_id}")
        return encounter

    def ingest_transcript(self, encounter: Encounter, raw_dictation_text: str) -> list[TranscriptSegment]:
        segments = self.transcription_agent.transcribe(encounter, raw_dictation_text)
        encounter.status = EncounterStatus.TRANSCRIBED
        self.audit_agent.log(encounter.id, "transcript_ingested", f"{len(segments)} segments")
        return segments

    def fetch_history(self, encounter: Encounter) -> str:
        summary = self.ehr_history_agent.fetch_summary(encounter.patient_id, self.ehr_client)
        self.audit_agent.log(encounter.id, "history_fetched", "patient history retrieved from EHR")
        return summary

    def generate_draft(
        self, encounter: Encounter, segments: list[TranscriptSegment], history_summary: str
    ) -> ClinicalNoteDraft:
        draft = self.drafting_agent.generate_draft(encounter, segments, history_summary)
        encounter.status = EncounterStatus.DRAFTED
        self.audit_agent.log(
            encounter.id, "draft_generated", f"generated_by={draft.generated_by.value}"
        )
        return draft

    def submit_review(self, encounter: Encounter, draft: ClinicalNoteDraft, edited_sections: dict, reviewer_id: str) -> NoteReview:
        review = self.review_agent.submit_review(draft, edited_sections, reviewer_id)
        encounter.status = EncounterStatus.REVIEWED
        self.audit_agent.log(encounter.id, "review_submitted", f"reviewer={reviewer_id}")
        return review

    def sign_and_deliver(self, encounter: Encounter, review: NoteReview) -> str:
        self.review_agent.sign(review)
        encounter.status = EncounterStatus.SIGNED
        document_id = self.ehr_client.push_signed_note(encounter.id, review.edited_sections)
        self.audit_agent.log(encounter.id, "note_signed_and_delivered", f"ehr_document_id={document_id}")
        return document_id
