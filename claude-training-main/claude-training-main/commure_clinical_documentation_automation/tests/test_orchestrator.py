from ehr_adapters import EHRAdapterRegistry
from llm_client import ClaudeClient
from models import EHRVendor, EncounterStatus, GeneratedBy
from orchestrator import MultiTenantPipeline
from sample_data import create_sample_encounters, seed_sample_tenants


def make_pipeline():
    # Force mock mode so tests never hit the network.
    return MultiTenantPipeline(llm_client=ClaudeClient(force_mock=True), adapter_registry=EHRAdapterRegistry())


def test_full_pipeline_end_to_end_across_tenants():
    pipeline = make_pipeline()
    tenants = seed_sample_tenants(pipeline)
    scenarios = create_sample_encounters()

    documents_by_vendor = {}
    for scenario in scenarios:
        tenant = tenants[scenario.tenant_label]
        encounter = pipeline.submit_encounter(
            tenant.id, scenario.clinician_id, scenario.specialty, scenario.raw_audio_text
        )

        assert encounter.tenant_id == tenant.id
        assert encounter.status == EncounterStatus.DELIVERED

        note = pipeline.get_note(tenant.id, encounter.id)
        assert note.generated_by == GeneratedBy.MOCK
        assert note.ehr_document_id is not None
        documents_by_vendor[tenant.ehr_vendor] = note.ehr_document_id

    assert documents_by_vendor[EHRVendor.EPIC].startswith("epic-doc-")
    assert documents_by_vendor[EHRVendor.CERNER].startswith("cerner-note-")
    assert documents_by_vendor[EHRVendor.ATHENAHEALTH].startswith("athena-doc-")


def test_metrics_are_isolated_per_tenant():
    pipeline = make_pipeline()
    tenants = seed_sample_tenants(pipeline)

    riverside = tenants["riverside"]
    lakeshore = tenants["lakeshore"]

    pipeline.submit_encounter(riverside.id, "dr-chen", "primary_care", "Encounter one.")
    pipeline.submit_encounter(riverside.id, "dr-chen", "primary_care", "Encounter two.")
    pipeline.submit_encounter(lakeshore.id, "dr-osei", "cardiology", "Encounter three.")

    riverside_metrics = pipeline.get_metrics(riverside.id)
    lakeshore_metrics = pipeline.get_metrics(lakeshore.id)

    assert riverside_metrics.encounters_delivered == 2
    assert lakeshore_metrics.encounters_delivered == 1


def test_unconfigured_specialty_falls_back_to_generic_soap_template():
    pipeline = make_pipeline()
    tenant = pipeline.register_tenant("Generic Health System", EHRVendor.EPIC, "us-east")

    encounter = pipeline.submit_encounter(tenant.id, "dr-doe", "dermatology", "Skin exam unremarkable.")
    note = pipeline.get_note(tenant.id, encounter.id)

    assert set(note.content_sections.keys()) == {"subjective", "objective", "assessment", "plan"}
