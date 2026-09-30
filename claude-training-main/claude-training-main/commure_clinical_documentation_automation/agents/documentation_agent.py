"""LLM Documentation Service Pool agent.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"LLM Documentation Service Pool" ("Generates structured notes per tenant's
template/specialty") and key processing step #3 ("Resolve tenant-specific
note templates and specialty vocabulary at generation time so one shared
LLM service pool can serve heterogeneous health systems").

Subscribes to `transcript.ready`, resolves the tenant's template for the
encounter's specialty from the Tenant Config Service, calls the shared
`ClaudeClient` with that template's section schema, and publishes
`note.generated`. This is the one agent in the pipeline that is genuinely
LLM-backed (falls back to a deterministic mock note offline, see
llm_client.py).
"""

from __future__ import annotations

from agents.base import BaseAgent
from encounter_store import EncounterStore
from llm_client import ClaudeClient
from models import Encounter, EncounterStatus, GeneratedBy, GeneratedNote
from streaming import Event, EventBus
from tenant_store import TenantConfigService


class DocumentationAgent(BaseAgent):
    name = "DocumentationAgent"

    def __init__(
        self,
        tenant_store: TenantConfigService,
        encounter_store: EncounterStore,
        llm_client: ClaudeClient,
        bus: EventBus,
    ):
        self.tenant_store = tenant_store
        self.encounter_store = encounter_store
        self.llm_client = llm_client
        self.bus = bus
        bus.subscribe("transcript.ready", self._on_transcript_ready)

    def _on_transcript_ready(self, event: Event) -> None:
        tenant_id = event.payload["tenant_id"]
        encounter_id = event.payload["encounter_id"]
        transcript = self.encounter_store.get_transcript(tenant_id, event.payload["transcript_id"])
        encounter = self.encounter_store.get_encounter(tenant_id, encounter_id)
        self.generate_note(encounter, transcript.text)

    def generate_note(self, encounter: Encounter, transcript_text: str) -> GeneratedNote:
        encounter.status = EncounterStatus.DRAFTING
        template = self.tenant_store.get_template(encounter.tenant_id, encounter.specialty)
        content_sections, generated_by = self.llm_client.generate_note(
            transcript_text, template.section_schema, encounter.specialty
        )
        note = GeneratedNote(
            encounter_id=encounter.id,
            tenant_id=encounter.tenant_id,
            content_sections=content_sections,
            generated_by=GeneratedBy(generated_by),
        )
        self.encounter_store.save_note(note)
        self.bus.publish(
            "note.generated",
            {"tenant_id": note.tenant_id, "encounter_id": note.encounter_id, "note_id": note.id},
        )
        return note
