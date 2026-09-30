"""Data models for the multi-tenant clinical documentation pipeline.

Mirrors the data models in
claude_in_healthcare/05-commure-clinical-documentation-automation.md (section 3.2).
Every record below carries a `tenant_id` — isolation is enforced at the model
level, not just at the API edge (see key processing step #1 in the design doc).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EHRVendor(str, Enum):
    EPIC = "epic"
    CERNER = "cerner"
    ATHENAHEALTH = "athenahealth"
    OTHER = "other"


class EncounterStatus(str, Enum):
    CAPTURING = "capturing"
    TRANSCRIBING = "transcribing"
    DRAFTING = "drafting"
    DELIVERED = "delivered"


class GeneratedBy(str, Enum):
    LLM = "llm"
    MOCK = "mock"


@dataclass
class NoteTemplate:
    tenant_id: str
    specialty: str
    section_schema: list[str]  # ordered section names, e.g. ["subjective", "objective", ...]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Tenant:
    health_system_name: str
    ehr_vendor: EHRVendor
    data_residency_region: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    note_templates: dict[str, NoteTemplate] = field(default_factory=dict)  # specialty -> template


@dataclass
class Encounter:
    tenant_id: str
    clinician_id: str
    specialty: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=_utcnow)
    status: EncounterStatus = EncounterStatus.CAPTURING


@dataclass
class Transcript:
    encounter_id: str
    tenant_id: str
    text: str
    asr_worker_id: str
    latency_ms: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class GeneratedNote:
    encounter_id: str
    tenant_id: str
    content_sections: dict  # {section_name: text}
    generated_by: GeneratedBy
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ehr_document_id: Optional[str] = None
    delivered_at: Optional[datetime] = None
