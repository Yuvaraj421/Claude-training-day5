"""Commure Clinical Documentation Automation — FastAPI demo.

Implements the representative API surface from
claude_in_healthcare/05-commure-clinical-documentation-automation.md (section 3.3)
on top of the `MultiTenantPipeline` orchestrator.

Educational demo only — not a real clinical system. All tenants, patients,
and transcripts used with it are synthetic. Run with:

    uvicorn main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from encounter_store import TenantIsolationError
from models import EHRVendor, Encounter
from orchestrator import MultiTenantPipeline

app = FastAPI(
    title="Commure Clinical Documentation Automation (Demo)",
    description=(
        "Illustrative multi-tenant ambient clinical documentation platform. "
        "Not a disclosure of Commure's real system — see claude_in_healthcare/"
        "05-commure-clinical-documentation-automation.md."
    ),
)

pipeline = MultiTenantPipeline()


class RegisterTenantRequest(BaseModel):
    health_system_name: str
    ehr_vendor: EHRVendor
    data_residency_region: str


class RegisterEncounterRequest(BaseModel):
    clinician_id: str
    specialty: str


class UploadAudioRequest(BaseModel):
    audio_text: str  # stand-in for an audio payload; see agents/ingestion_agent.py


class SetTemplateRequest(BaseModel):
    section_schema: list[str]


def _tenant_or_404(tenant_id: str):
    tenant = pipeline.tenant_store.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Unknown tenant_id: {tenant_id}")
    return tenant


@app.post("/v1/tenants")
def register_tenant(body: RegisterTenantRequest):
    tenant = pipeline.register_tenant(body.health_system_name, body.ehr_vendor, body.data_residency_region)
    return {
        "id": tenant.id,
        "health_system_name": tenant.health_system_name,
        "ehr_vendor": tenant.ehr_vendor.value,
        "data_residency_region": tenant.data_residency_region,
    }


@app.put("/v1/tenants/{tenant_id}/templates/{specialty}")
def set_template(tenant_id: str, specialty: str, body: SetTemplateRequest):
    _tenant_or_404(tenant_id)
    template = pipeline.set_template(tenant_id, specialty, body.section_schema)
    return {"id": template.id, "specialty": template.specialty, "section_schema": template.section_schema}


@app.post("/v1/tenants/{tenant_id}/encounters")
def register_encounter(tenant_id: str, body: RegisterEncounterRequest):
    """Registers an encounter. Audio is uploaded separately via the /audio endpoint below."""
    _tenant_or_404(tenant_id)
    # Registration without audio: create the Encounter record directly so callers can
    # reference `id` before any audio exists, matching the doc's two-step capture flow.
    encounter = Encounter(tenant_id=tenant_id, clinician_id=body.clinician_id, specialty=body.specialty)
    pipeline.encounter_store.save_encounter(encounter)
    return {"id": encounter.id, "status": encounter.status.value}


@app.post("/v1/tenants/{tenant_id}/encounters/{encounter_id}/audio")
def upload_audio(tenant_id: str, encounter_id: str, body: UploadAudioRequest):
    """Feeds captured audio into the pipeline: ASR -> LLM documentation -> EHR delivery.

    In this synchronous demo the whole pipeline (including EHR delivery) completes
    before this call returns, standing in for what would be an asynchronous,
    horizontally-scaled flow across the streaming backbone in production.
    """
    _tenant_or_404(tenant_id)
    try:
        encounter = pipeline.encounter_store.get_encounter(tenant_id, encounter_id)
    except (KeyError, TenantIsolationError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Publish onto the bus rather than calling TranscriptionAgent directly — this
    # synchronously fans out through ASR -> LLM documentation -> EHR delivery
    # before the call returns, same as agents talking to each other in production.
    pipeline.bus.publish(
        "encounter.audio",
        {"tenant_id": tenant_id, "encounter_id": encounter.id, "audio_text": body.audio_text},
    )
    return {"id": encounter.id, "status": encounter.status.value}


@app.get("/v1/tenants/{tenant_id}/encounters/{encounter_id}/note")
def get_note(tenant_id: str, encounter_id: str):
    _tenant_or_404(tenant_id)
    try:
        encounter = pipeline.encounter_store.get_encounter(tenant_id, encounter_id)
        note = pipeline.get_note(tenant_id, encounter_id)
    except (KeyError, TenantIsolationError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if note is None:
        return {"encounter_id": encounter_id, "status": encounter.status.value, "note": None}
    return {
        "encounter_id": encounter_id,
        "status": encounter.status.value,
        "note": {
            "id": note.id,
            "content_sections": note.content_sections,
            "generated_by": note.generated_by.value,
            "ehr_document_id": note.ehr_document_id,
            "delivered_at": note.delivered_at.isoformat() if note.delivered_at else None,
        },
    }


@app.post("/v1/tenants/{tenant_id}/encounters/{encounter_id}/deliver")
def deliver_note(tenant_id: str, encounter_id: str):
    """Pushes the finalized note to the tenant's EHR.

    In this demo, delivery already happens automatically once the note is
    generated (see agents/delivery_agent.py subscribing to `note.generated`),
    so this endpoint is idempotent: it returns the existing delivery result,
    matching the doc's API surface for platforms where delivery is a
    separate, explicitly-triggered step.
    """
    _tenant_or_404(tenant_id)
    try:
        note = pipeline.get_note(tenant_id, encounter_id)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if note is None:
        raise HTTPException(status_code=409, detail="Note not yet generated for this encounter")
    if note.ehr_document_id is None:
        document_id = pipeline.delivery_agent.deliver(note)
    else:
        document_id = note.ehr_document_id
    return {"encounter_id": encounter_id, "ehr_document_id": document_id}


@app.get("/v1/tenants/{tenant_id}/metrics/throughput")
def get_throughput(tenant_id: str):
    _tenant_or_404(tenant_id)
    metrics = pipeline.get_metrics(tenant_id)
    return {
        "tenant_id": tenant_id,
        "encounters_captured": metrics.encounters_captured,
        "transcripts_completed": metrics.transcripts_completed,
        "notes_generated": metrics.notes_generated,
        "encounters_delivered": metrics.encounters_delivered,
        "avg_asr_latency_ms": metrics.avg_asr_latency_ms,
    }
