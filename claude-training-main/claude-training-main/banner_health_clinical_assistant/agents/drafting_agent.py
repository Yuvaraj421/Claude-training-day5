"""Clinical LLM drafting agent.

Doc reference: 01-banner-health-clinical-documentation.md, component "Clinical LLM Drafting Service"
and key processing step #3 ("generate the note in structured sections").
"""

from __future__ import annotations

from typing import List

from agents.base import BaseAgent
from llm_client import ClaudeClient
from models import ClinicalNoteDraft, Encounter, GeneratedBy, TranscriptSegment


class DraftingAgent(BaseAgent):
    name = "DraftingAgent"

    def __init__(self, llm_client: ClaudeClient):
        self.llm_client = llm_client

    def generate_draft(
        self,
        encounter: Encounter,
        transcript_segments: List[TranscriptSegment],
        history_summary: str,
    ) -> ClinicalNoteDraft:
        transcript_text = " ".join(seg.text for seg in transcript_segments)
        sections, generated_by = self.llm_client.generate_note(transcript_text, history_summary)
        return ClinicalNoteDraft(
            encounter_id=encounter.id,
            sections=sections,
            generated_by=GeneratedBy(generated_by),
        )
