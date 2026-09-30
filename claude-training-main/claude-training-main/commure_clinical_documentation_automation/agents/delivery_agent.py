"""EHR delivery agent — the pipeline-facing side of the EHR Adapter Layer.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"EHR Adapter Layer" and key processing step #4 ("Abstract EHR differences
behind a per-vendor adapter layer so the documentation pipeline itself stays
EHR-agnostic").

Subscribes to `note.generated`, routes to the tenant's configured EHR vendor
via `EHRAdapterRegistry`, and publishes `encounter.completed` once the
adapter confirms delivery. The pipeline never talks to a vendor adapter
directly — it only ever asks the registry for "this tenant's adapter".
"""

from __future__ import annotations

from datetime import datetime, timezone

from agents.base import BaseAgent
from ehr_adapters import EHRAdapterRegistry
from encounter_store import EncounterStore
from models import EncounterStatus, GeneratedNote
from streaming import Event, EventBus
from tenant_store import TenantConfigService


class DeliveryAgent(BaseAgent):
    name = "DeliveryAgent"

    def __init__(
        self,
        tenant_store: TenantConfigService,
        encounter_store: EncounterStore,
        adapter_registry: EHRAdapterRegistry,
        bus: EventBus,
    ):
        self.tenant_store = tenant_store
        self.encounter_store = encounter_store
        self.adapter_registry = adapter_registry
        self.bus = bus
        bus.subscribe("note.generated", self._on_note_generated)

    def _on_note_generated(self, event: Event) -> None:
        tenant_id = event.payload["tenant_id"]
        note = self.encounter_store.get_note(tenant_id, event.payload["note_id"])
        self.deliver(note)

    def deliver(self, note: GeneratedNote) -> str:
        tenant = self.tenant_store.require_tenant(note.tenant_id)
        adapter = self.adapter_registry.get(tenant.ehr_vendor)

        document_id = adapter.push_note(tenant, note)
        note.ehr_document_id = document_id
        note.delivered_at = datetime.now(timezone.utc)

        encounter = self.encounter_store.get_encounter(note.tenant_id, note.encounter_id)
        encounter.status = EncounterStatus.DELIVERED

        self.bus.publish(
            "encounter.completed",
            {
                "tenant_id": note.tenant_id,
                "encounter_id": note.encounter_id,
                "note_id": note.id,
                "ehr_document_id": document_id,
                "ehr_vendor": tenant.ehr_vendor.value,
            },
        )
        return document_id
