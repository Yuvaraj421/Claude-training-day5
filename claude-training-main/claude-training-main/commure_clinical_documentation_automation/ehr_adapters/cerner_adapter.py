"""Cerner (Oracle Health) adapter — simulates its proprietary note-write API.

Cerner's public API historically has weaker FHIR write support for clinical
notes than Epic's, so this adapter models a vendor-specific note payload
shape instead of a generic FHIR resource.
"""

from __future__ import annotations

import uuid

from models import GeneratedNote, Tenant

from .base import EHRAdapter


class CernerAdapter(EHRAdapter):
    vendor = "cerner"

    def __init__(self):
        self._written_documents: dict[str, dict] = {}

    def push_note(self, tenant: Tenant, note: GeneratedNote) -> str:
        document_id = f"cerner-note-{uuid.uuid4().hex[:8]}"
        cerner_payload = {
            "noteType": "AmbientEncounterNote",
            "sections": [
                {"sectionName": section, "sectionText": text}
                for section, text in note.content_sections.items()
            ],
        }
        self._written_documents[document_id] = cerner_payload
        return document_id
