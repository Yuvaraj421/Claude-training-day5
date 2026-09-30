"""athenahealth adapter — simulates its REST-based clinical document API.

athenahealth's API is REST/JSON-based rather than FHIR-native for note
write-back, so this adapter models a flat JSON document payload.
"""

from __future__ import annotations

import uuid

from models import GeneratedNote, Tenant

from .base import EHRAdapter


class AthenahealthAdapter(EHRAdapter):
    vendor = "athenahealth"

    def __init__(self):
        self._written_documents: dict[str, dict] = {}

    def push_note(self, tenant: Tenant, note: GeneratedNote) -> str:
        document_id = f"athena-doc-{uuid.uuid4().hex[:8]}"
        athena_payload = {"documenttypeid": "CLINICALNOTE", "content": dict(note.content_sections)}
        self._written_documents[document_id] = athena_payload
        return document_id
