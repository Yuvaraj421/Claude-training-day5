"""Data models for the clinical documentation pipeline.

Mirrors the data models in claude_in_healthcare/01-banner-health-clinical-documentation.md (section 3.2).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EncounterStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    TRANSCRIBED = "transcribed"
    DRAFTED = "drafted"
    REVIEWED = "reviewed"
    SIGNED = "signed"


class SpeakerRole(str, Enum):
    CLINICIAN = "clinician"
    PATIENT = "patient"
    OTHER = "other"


class GeneratedBy(str, Enum):
    LLM = "llm"
    MOCK = "mock"
    CLINICIAN_EDIT = "clinician_edit"


@dataclass
class Encounter:
    patient_id: str
    provider_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=_utcnow)
    ended_at: Optional[datetime] = None
    status: EncounterStatus = EncounterStatus.IN_PROGRESS


@dataclass
class TranscriptSegment:
    encounter_id: str
    sequence: int
    text: str
    speaker_role: SpeakerRole
    confidence: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ClinicalNoteDraft:
    encounter_id: str
    sections: dict  # {"subjective": str, "objective": str, "assessment": str, "plan": str}
    generated_by: GeneratedBy
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class NoteReview:
    draft_id: str
    reviewer_id: str
    edited_sections: dict
    edits_diff: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    approved: bool = False
    signed_at: Optional[datetime] = None
