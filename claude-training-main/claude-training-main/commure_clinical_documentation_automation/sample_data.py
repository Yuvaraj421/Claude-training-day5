"""Synthetic sample tenants and encounter scenarios for the demo.

All health system names, clinicians, and dictation text below are fabricated
for demonstration purposes only and do not represent real organizations or
real records.
"""

from __future__ import annotations

from dataclasses import dataclass

from models import EHRVendor, Tenant
from orchestrator import MultiTenantPipeline


@dataclass
class SampleScenario:
    label: str
    tenant_label: str
    clinician_id: str
    specialty: str
    raw_audio_text: str


def seed_sample_tenants(pipeline: MultiTenantPipeline) -> dict[str, Tenant]:
    """Registers a few health-system tenants on different EHR vendors, each
    with its own note template, and returns them keyed by a short label."""
    tenants: dict[str, Tenant] = {}

    tenants["riverside"] = pipeline.register_tenant(
        health_system_name="Riverside Health Network",
        ehr_vendor=EHRVendor.EPIC,
        data_residency_region="us-east",
    )
    pipeline.set_template(
        tenants["riverside"].id,
        specialty="primary_care",
        section_schema=["subjective", "objective", "assessment", "plan"],
    )

    tenants["lakeshore"] = pipeline.register_tenant(
        health_system_name="Lakeshore Medical Group",
        ehr_vendor=EHRVendor.CERNER,
        data_residency_region="us-central",
    )
    pipeline.set_template(
        tenants["lakeshore"].id,
        specialty="cardiology",
        section_schema=["chief_complaint", "history", "findings", "impression", "recommendations"],
    )

    tenants["summit"] = pipeline.register_tenant(
        health_system_name="Summit Regional Clinics",
        ehr_vendor=EHRVendor.ATHENAHEALTH,
        data_residency_region="us-west",
    )
    pipeline.set_template(
        tenants["summit"].id,
        specialty="pediatrics",
        section_schema=["subjective", "growth_and_development", "exam", "plan"],
    )

    return tenants


def create_sample_encounters() -> list[SampleScenario]:
    return [
        SampleScenario(
            label="Riverside — routine primary care follow-up",
            tenant_label="riverside",
            clinician_id="dr-chen",
            specialty="primary_care",
            raw_audio_text=(
                "Patient here for routine follow-up. Reports good adherence to metformin and no "
                "hypoglycemia episodes. Blood pressure 128 over 78, weight stable. Plan is to "
                "continue current regimen and recheck A1c in three months."
            ),
        ),
        SampleScenario(
            label="Lakeshore — cardiology consult",
            tenant_label="lakeshore",
            clinician_id="dr-osei",
            specialty="cardiology",
            raw_audio_text=(
                "Patient presents with intermittent palpitations over the past two weeks, no chest "
                "pain or syncope. ECG shows normal sinus rhythm. Recommending 48-hour Holter monitor "
                "and follow-up in two weeks to review results."
            ),
        ),
        SampleScenario(
            label="Summit — pediatric well-child visit",
            tenant_label="summit",
            clinician_id="dr-patel",
            specialty="pediatrics",
            raw_audio_text=(
                "Well-child visit for a healthy four-year-old. Growth tracking along the 60th "
                "percentile for height and weight. Vaccinations up to date. No parental concerns "
                "today. Plan is routine follow-up at the next scheduled well-child visit."
            ),
        ),
    ]
