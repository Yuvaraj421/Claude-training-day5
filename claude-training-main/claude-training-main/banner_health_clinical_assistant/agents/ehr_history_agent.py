"""EHR record summarization agent.

Doc reference: 01-banner-health-clinical-documentation.md, component "Record Summarization Service"
and key processing step #2 ("retrieve only the minimum necessary patient history").
"""

from __future__ import annotations

from agents.base import BaseAgent
from ehr_mock import EHRSystemMock


class EHRHistoryAgent(BaseAgent):
    name = "EHRHistoryAgent"

    def fetch_summary(self, patient_id: str, ehr_client: EHRSystemMock) -> str:
        history = ehr_client.get_patient_history(patient_id)
        if history is None:
            return "No prior history on file for this patient."

        lines = [
            f"Patient: {history['name']} (DOB {history['dob']})",
            f"Problem list: {', '.join(history['problem_list']) or 'None documented'}",
            f"Current medications: {', '.join(history['medications']) or 'None documented'}",
            f"Allergies: {', '.join(history['allergies']) or 'None documented'}",
        ]
        if history["recent_notes"]:
            lines.append(f"Most recent note: {history['recent_notes'][-1]}")
        return "\n".join(lines)
