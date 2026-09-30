from agents.delivery_agent import DeliveryAgent
from agents.documentation_agent import DocumentationAgent
from agents.ingestion_agent import IngestionAgent
from agents.monitoring_agent import MonitoringAgent
from agents.transcription_agent import TranscriptionAgent
from ehr_adapters import EHRAdapterRegistry
from encounter_store import EncounterStore
from llm_client import ClaudeClient
from models import EHRVendor, Encounter, EncounterStatus, GeneratedBy
from streaming import EventBus
from tenant_store import TenantConfigService


def make_wired_agents():
    tenant_store = TenantConfigService()
    encounter_store = EncounterStore()
    bus = EventBus()
    ingestion = IngestionAgent(tenant_store, encounter_store, bus)
    transcription = TranscriptionAgent(encounter_store, bus)
    documentation = DocumentationAgent(tenant_store, encounter_store, ClaudeClient(force_mock=True), bus)
    delivery = DeliveryAgent(tenant_store, encounter_store, EHRAdapterRegistry(), bus)
    monitoring = MonitoringAgent(bus)
    return tenant_store, encounter_store, bus, ingestion, transcription, documentation, delivery, monitoring


def test_ingestion_agent_tags_tenant_id_and_publishes_encounter_audio():
    tenant_store, encounter_store, bus, ingestion, *_ = make_wired_agents()
    tenant = tenant_store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")

    # capture() publishes onto the bus, which synchronously fans out through the
    # whole pipeline (ASR -> LLM -> EHR delivery) before this call returns.
    encounter = ingestion.capture(tenant.id, "dr-chen", "primary_care", "Patient feels well today.")

    assert encounter.tenant_id == tenant.id
    assert encounter.status == EncounterStatus.DELIVERED
    events = bus.events("encounter.audio")
    assert len(events) == 1
    assert events[0].payload["tenant_id"] == tenant.id


def _store_with_encounter(tenant_id: str, encounter_id: str) -> EncounterStore:
    store = EncounterStore()
    store.save_encounter(Encounter(tenant_id=tenant_id, clinician_id="dr-chen", specialty="primary_care", id=encounter_id))
    return store


def test_transcription_agent_produces_deterministic_worker_assignment():
    transcript_a = TranscriptionAgent(_store_with_encounter("t1", "enc-1"), EventBus()).transcribe(
        "t1", "enc-1", "Hello there."
    )
    transcript_b = TranscriptionAgent(_store_with_encounter("t1", "enc-1"), EventBus()).transcribe(
        "t1", "enc-1", "Hello there."
    )

    assert transcript_a.asr_worker_id == transcript_b.asr_worker_id
    assert transcript_a.latency_ms == transcript_b.latency_ms
    assert transcript_a.text == "Hello there."


def test_documentation_agent_uses_tenant_template_section_schema():
    tenant_store, encounter_store, bus, ingestion, transcription, documentation, *_ = make_wired_agents()
    tenant = tenant_store.register_tenant("Lakeshore Medical Group", EHRVendor.CERNER, "us-central")
    tenant_store.set_template(tenant.id, "cardiology", ["chief_complaint", "history", "plan"])

    encounter = ingestion.capture(tenant.id, "dr-osei", "cardiology", "Patient reports palpitations.")
    note = encounter_store.get_note_for_encounter(tenant.id, encounter.id)

    assert note.generated_by == GeneratedBy.MOCK
    assert set(note.content_sections.keys()) == {"chief_complaint", "history", "plan"}


def test_delivery_agent_routes_to_tenants_ehr_vendor():
    tenant_store, encounter_store, bus, ingestion, *_ = make_wired_agents()
    tenant = tenant_store.register_tenant("Summit Regional Clinics", EHRVendor.ATHENAHEALTH, "us-west")

    encounter = ingestion.capture(tenant.id, "dr-patel", "pediatrics", "Well-child visit, no concerns.")
    note = encounter_store.get_note_for_encounter(tenant.id, encounter.id)

    assert note.ehr_document_id.startswith("athena-doc-")
    assert encounter.status == EncounterStatus.DELIVERED


def test_monitoring_agent_tracks_per_tenant_throughput():
    tenant_store, encounter_store, bus, ingestion, *_, monitoring = make_wired_agents()
    tenant = tenant_store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")

    ingestion.capture(tenant.id, "dr-chen", "primary_care", "First encounter.")
    ingestion.capture(tenant.id, "dr-chen", "primary_care", "Second encounter.")

    metrics = monitoring.get_metrics(tenant.id)
    assert metrics.encounters_captured == 2
    assert metrics.encounters_delivered == 2
    assert metrics.notes_generated == 2
