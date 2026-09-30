"""Epic adapter — simulates writing a FHIR DocumentReference via SMART on FHIR.

Epic has the most mature FHIR support of the three vendors modeled here, so
this adapter maps sections directly onto a FHIR DocumentReference-shaped
payload without any vendor-specific translation.
"""

from __future__ import annotations

import uuid

from models import GeneratedNote, Tenant

from .base import EHRAdapter


class EpicAdapter(EHRAdapter):
    vendor = "epic"

    def __init__(self):
        self._written_documents: dict[str, dict] = {}

    def push_note(self, tenant: Tenant, note: GeneratedNote) -> str:
        document_id = f"epic-doc-{uuid.uuid4().hex[:8]}"
        fhir_document_reference = {
            "resourceType": "DocumentReference",
            "status": "current",
            "content": [
                {"attachment": {"title": section, "data": text}}
                for section, text in note.content_sections.items()
            ],
        }
        self._written_documents[document_id] = fhir_document_reference
        return document_id
