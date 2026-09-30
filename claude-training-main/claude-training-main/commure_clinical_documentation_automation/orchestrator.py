"""Multi-tenant encounter pipeline orchestrator.

Wires the agents onto a shared `EventBus` in the exact order of the sequence
diagram in claude_in_healthcare/05-commure-clinical-documentation-automation.md
(section 3.1): capture -> edge ingestion -> streaming backbone -> ASR ->
streaming backbone -> LLM documentation (tenant template resolved) -> EHR
adapter -> tenant's EHR -> completion event -> monitoring.

Unlike a single-tenant pipeline, `submit_encounter` is the only entry point
and takes a `tenant_id` on every call — everything downstream (template,
EHR vendor, adapter, isolation checks) is resolved from that one ID.
"""

from __future__ import annotations

from agents import DeliveryAgent, DocumentationAgent, IngestionAgent, MonitoringAgent, TranscriptionAgent
from agents.monitoring_agent import TenantMetrics
from ehr_adapters import EHRAdapterRegistry
from encounter_store import EncounterStore
from llm_client import ClaudeClient
from models import EHRVendor, Encounter, GeneratedNote, NoteTemplate, Tenant
from streaming import EventBus
from tenant_store import TenantConfigService


class MultiTenantPipeline:
    def __init__(self, llm_client: ClaudeClient | None = None, adapter_registry: EHRAdapterRegistry | None = None):
        self.tenant_store = TenantConfigService()
        self.encounter_store = EncounterStore()
        self.bus = EventBus()
        self.adapter_registry = adapter_registry or EHRAdapterRegistry()

        self.ingestion_agent = IngestionAgent(self.tenant_store, self.encounter_store, self.bus)
        self.transcription_agent = TranscriptionAgent(self.encounter_store, self.bus)
        self.documentation_agent = DocumentationAgent(
            self.tenant_store, self.encounter_store, llm_client or ClaudeClient(), self.bus
        )
        self.delivery_agent = DeliveryAgent(self.tenant_store, self.encounter_store, self.adapter_registry, self.bus)
        self.monitoring_agent = MonitoringAgent(self.bus)

    # -- Tenant onboarding --------------------------------------------------
    def register_tenant(self, health_system_name: str, ehr_vendor: EHRVendor, data_residency_region: str) -> Tenant:
        return self.tenant_store.register_tenant(health_system_name, ehr_vendor, data_residency_region)

    def set_template(self, tenant_id: str, specialty: str, section_schema: list[str]) -> NoteTemplate:
        return self.tenant_store.set_template(tenant_id, specialty, section_schema)

    # -- Encounter flow -------------------------------------------------------
    def submit_encounter(self, tenant_id: str, clinician_id: str, specialty: str, raw_audio_text: str) -> Encounter:
        """Runs one encounter end-to-end through capture -> ASR -> LLM -> EHR delivery.

        The EventBus dispatches synchronously, so by the time this call
        returns the encounter's GeneratedNote has been delivered and its
        status is DELIVERED — this call is the demo's stand-in for what
        would be an asynchronous, horizontally-scaled pipeline in production.
        """
        return self.ingestion_agent.capture(tenant_id, clinician_id, specialty, raw_audio_text)

    def get_note(self, tenant_id: str, encounter_id: str) -> GeneratedNote | None:
        return self.encounter_store.get_note_for_encounter(tenant_id, encounter_id)

    def get_metrics(self, tenant_id: str) -> TenantMetrics:
        return self.monitoring_agent.get_metrics(tenant_id)
