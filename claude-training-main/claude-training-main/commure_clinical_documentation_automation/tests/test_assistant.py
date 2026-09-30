from assistant import PlatformAssistant
from models import EHRVendor
from orchestrator import MultiTenantPipeline


def _pipeline_with_tenant():
    pipeline = MultiTenantPipeline()
    pipeline.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")
    return pipeline


def test_mock_assistant_is_not_live():
    assistant = PlatformAssistant(force_mock=True)
    assert assistant.is_live is False


def test_mock_assistant_lists_tenants():
    pipeline = _pipeline_with_tenant()
    assistant = PlatformAssistant(force_mock=True)
    reply = assistant.respond(pipeline, [], "list tenants")
    assert "Riverside Health Network" in reply
    assert "epic" in reply


def test_mock_assistant_reports_metrics_for_named_tenant():
    pipeline = _pipeline_with_tenant()
    tenant = pipeline.tenant_store.list_tenants()[0]
    pipeline.submit_encounter(tenant.id, "dr-demo", "primary_care", "Patient reports mild headache.")
    assistant = PlatformAssistant(force_mock=True)
    reply = assistant.respond(pipeline, [], "metrics for riverside")
    assert "delivered=1" in reply


def test_mock_assistant_unknown_tenant_reports_error():
    pipeline = _pipeline_with_tenant()
    assistant = PlatformAssistant(force_mock=True)
    reply = assistant.respond(pipeline, [], "metrics for nonexistent health system")
    assert "No tenant matching" in reply


def test_mock_assistant_falls_back_to_help_for_unrecognized_input():
    pipeline = _pipeline_with_tenant()
    assistant = PlatformAssistant(force_mock=True)
    reply = assistant.respond(pipeline, [], "what's the weather like")
    assert "recognized commands" in reply


def test_submit_encounter_tool_runs_full_pipeline():
    from assistant import _execute_tool

    pipeline = _pipeline_with_tenant()
    tenant = pipeline.tenant_store.list_tenants()[0]
    result = _execute_tool(
        pipeline,
        "submit_encounter",
        {
            "tenant": tenant.id,
            "clinician_id": "dr-demo",
            "specialty": "primary_care",
            "audio_text": "Patient reports mild headache.",
        },
    )
    assert result["status"] == "delivered"
    assert result["ehr_document_id"].startswith("epic-doc-")
