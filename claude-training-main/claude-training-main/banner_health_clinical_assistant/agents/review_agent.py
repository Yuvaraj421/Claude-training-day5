"""Clinician review agent.

Doc reference: 01-banner-health-clinical-documentation.md, component "Clinician Review UI"
and key processing steps #4 ("track diff between AI draft and clinician-signed version")
and #5 ("never auto-submit to EHR without an explicit sign-off action").
"""

from __future__ import annotations

import difflib
from datetime import datetime, timezone

from agents.base import BaseAgent
from models import ClinicalNoteDraft, NoteReview


class ReviewAgent(BaseAgent):
    name = "ReviewAgent"

    def submit_review(self, draft: ClinicalNoteDraft, edited_sections: dict, reviewer_id: str) -> NoteReview:
        diff = self._diff_sections(draft.sections, edited_sections)
        return NoteReview(
            draft_id=draft.id,
            reviewer_id=reviewer_id,
            edited_sections=edited_sections,
            edits_diff=diff,
        )

    def sign(self, review: NoteReview) -> NoteReview:
        review.approved = True
        review.signed_at = datetime.now(timezone.utc)
        return review

    @staticmethod
    def _diff_sections(original: dict, edited: dict) -> str:
        diff_lines = []
        for section in ("subjective", "objective", "assessment", "plan"):
            original_text = original.get(section, "")
            edited_text = edited.get(section, "")
            if original_text == edited_text:
                continue
            section_diff = difflib.unified_diff(
                original_text.splitlines(),
                edited_text.splitlines(),
                lineterm="",
                fromfile=f"{section} (AI draft)",
                tofile=f"{section} (clinician edit)",
            )
            diff_lines.extend(section_diff)
        return "\n".join(diff_lines) if diff_lines else "No edits — signed as drafted."
