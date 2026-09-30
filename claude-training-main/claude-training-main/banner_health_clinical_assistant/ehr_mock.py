"""In-memory mock EHR system.

Doc reference: 01-banner-health-clinical-documentation.md, "EHR System (e.g. Cerner / Epic)"
and the API surface's FHIR-style Patient/Condition/MedicationRequest/Observation retrieval.

This stands in for a real SMART on FHIR integration: no network calls, just a
small set of synthetic patients so the demo can run end-to-end offline.
"""

from __future__ import annotations

import uuid
from typing import Optional

_PATIENTS = {
    "pt-1001": {
        "name": "Jordan Alvarez",
        "dob": "1978-04-12",
        "problem_list": ["Type 2 diabetes mellitus", "Hyperlipidemia"],
        "medications": ["Metformin 1000mg BID", "Atorvastatin 20mg QHS"],
        "allergies": ["Penicillin"],
        "recent_notes": [
            "3 months ago: A1c 7.2%, continue current regimen, recheck in 3 months.",
        ],
    },
    "pt-1002": {
        "name": "Priya Nair",
        "dob": "1990-11-02",
        "problem_list": ["Essential hypertension"],
        "medications": ["Lisinopril 10mg daily"],
        "allergies": ["No known drug allergies"],
        "recent_notes": [
            "6 months ago: BP 138/88, started lisinopril, f/u in 4-6 weeks.",
        ],
    },
    "pt-1003": {
        "name": "Marcus Webb",
        "dob": "1965-07-23",
        "problem_list": ["GERD", "Seasonal allergic rhinitis"],
        "medications": ["Omeprazole 20mg daily", "Loratadine 10mg PRN"],
        "allergies": ["Sulfa drugs"],
        "recent_notes": [
            "1 year ago: Symptoms well controlled on current regimen.",
        ],
    },
}


class EHRSystemMock:
    """Simulates a FHIR-capable EHR: patient history lookup + signed-note write-back."""

    def __init__(self):
        self._signed_notes = {}

    def get_patient_history(self, patient_id: str) -> Optional[dict]:
        return _PATIENTS.get(patient_id)

    def push_signed_note(self, encounter_id: str, note_sections: dict) -> str:
        """Simulates POSTing a signed DocumentReference back to the EHR."""
        document_id = f"doc-{uuid.uuid4().hex[:8]}"
        self._signed_notes[document_id] = {
            "encounter_id": encounter_id,
            "sections": note_sections,
        }
        return document_id
