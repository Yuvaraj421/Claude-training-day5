"""Ambient capture + edge/regional ingestion agent.

Doc reference: 05-commure-clinical-documentation-automation.md, components
"Ambient Capture Clients" and "Edge/Regional Ingestion" ("Regional intake
points to reduce latency and meet data-residency needs") and key processing
step #1 ("Tag every record with tenant_id from ingestion onward").

There is no real microphone/audio pipeline in this demo, so `capture()`
takes already-dictated text (standing in for ambient audio) and is
responsible for the one thing the design doc calls out as happening at this
stage: stamping every downstream record with the originating tenant_id
before anything is published to the streaming backbone.
"""

from __future__ import annotations

from agents.base import BaseAgent
from encounter_store import EncounterStore
from models import Encounter
from streaming import EventBus
from tenant_store import TenantConfigService


class IngestionAgent(BaseAgent):
    name = "IngestionAgent"

    def __init__(self, tenant_store: TenantConfigService, encounter_store: EncounterStore, bus: EventBus):
        self.tenant_store = tenant_store
        self.encounter_store = encounter_store
        self.bus = bus

    def capture(self, tenant_id: str, clinician_id: str, specialty: str, raw_audio_text: str) -> Encounter:
        tenant = self.tenant_store.require_tenant(tenant_id)  # fail fast on unknown tenant
        encounter = Encounter(tenant_id=tenant.id, clinician_id=clinician_id, specialty=specialty)
        self.encounter_store.save_encounter(encounter)
        self.bus.publish(
            "encounter.audio",
            {
                "tenant_id": tenant.id,
                "encounter_id": encounter.id,
                "region": tenant.data_residency_region,
                "audio_text": raw_audio_text,
            },
        )
        return encounter
