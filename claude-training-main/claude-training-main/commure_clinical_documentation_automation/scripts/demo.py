"""Console walkthrough of the multi-tenant encounter pipeline.

Run from the project root:

    python scripts/demo.py

Seeds three health-system tenants on three different EHR vendors, submits a
sample encounter for each, and prints the resulting note, EHR document ID,
and per-tenant throughput metrics — then demonstrates that the encounter
store refuses a cross-tenant read.

Educational demo only. All tenants, clinicians, and transcripts are synthetic.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from encounter_store import TenantIsolationError
from orchestrator import MultiTenantPipeline
from sample_data import create_sample_encounters, seed_sample_tenants


def main() -> None:
    pipeline = MultiTenantPipeline()
    tenants = seed_sample_tenants(pipeline)

    if pipeline.documentation_agent.llm_client.is_live:
        print("Live mode: documentation generated via the Anthropic API (Claude).\n")
    else:
        print(
            "Mock mode: no ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN found — using a "
            "templated note generator instead of a live Claude call.\n"
        )

    encounters_by_scenario = {}
    for scenario in create_sample_encounters():
        tenant = tenants[scenario.tenant_label]
        print(f"=== {scenario.label} (tenant={tenant.health_system_name}, ehr={tenant.ehr_vendor.value}) ===")

        encounter = pipeline.submit_encounter(
            tenant_id=tenant.id,
            clinician_id=scenario.clinician_id,
            specialty=scenario.specialty,
            raw_audio_text=scenario.raw_audio_text,
        )
        encounters_by_scenario[scenario.label] = (tenant.id, encounter.id)

        note = pipeline.get_note(tenant.id, encounter.id)
        print(f"Encounter status: {encounter.status.value}")
        for section, text in note.content_sections.items():
            print(f"  [{section}] {text}")
        print(f"EHR document ID ({tenant.ehr_vendor.value}): {note.ehr_document_id}")

        metrics = pipeline.get_metrics(tenant.id)
        print(
            f"Tenant throughput so far: captured={metrics.encounters_captured} "
            f"delivered={metrics.encounters_delivered} avg_asr_latency_ms={metrics.avg_asr_latency_ms}"
        )
        print()

    print("=== Tenant isolation check ===")
    (tenant_a_id, encounter_a_id) = encounters_by_scenario["Riverside — routine primary care follow-up"]
    (tenant_b_id, _) = encounters_by_scenario["Lakeshore — cardiology consult"]
    try:
        pipeline.encounter_store.get_encounter(tenant_b_id, encounter_a_id)
        print("UNEXPECTED: cross-tenant read succeeded — isolation is broken!")
    except TenantIsolationError as exc:
        print(f"Blocked as expected: {exc}")


if __name__ == "__main__":
    main()
