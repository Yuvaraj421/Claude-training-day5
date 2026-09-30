"""Synthetic sample encounter scenarios for the demo UI.

All patient names, histories, and dictation text below are fabricated for
demonstration purposes only and do not represent real people or real records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SampleScenario:
    label: str
    patient_id: str
    provider_id: str
    raw_dictation_text: str


def create_sample_encounters() -> list[SampleScenario]:
    return [
        SampleScenario(
            label="Routine diabetes follow-up — Jordan Alvarez",
            patient_id="pt-1001",
            provider_id="dr-chen",
            raw_dictation_text=(
                "Patient here for routine diabetes follow-up. Reports good adherence to metformin "
                "and no episodes of hypoglycemia. Denies polyuria, polydipsia, or blurred vision. "
                "Blood pressure 128 over 78, weight stable at 182 pounds. Feet examined, no ulcers "
                "or signs of neuropathy noted. Plan is to continue current metformin dose, order a "
                "repeat A1c, and follow up in three months."
            ),
        ),
        SampleScenario(
            label="New hypertension diagnosis — Priya Nair",
            patient_id="pt-1002",
            provider_id="dr-osei",
            raw_dictation_text=(
                "Patient presents with elevated blood pressure readings at home averaging 148 over "
                "92 over the past two weeks. No headache, chest pain, or vision changes. Family "
                "history of hypertension on mother's side. Exam is unremarkable, blood pressure "
                "today 144 over 90. Discussed lifestyle modification including reduced sodium "
                "intake and regular exercise. Continuing lisinopril at current dose and scheduling "
                "follow-up in four to six weeks to reassess."
            ),
        ),
        SampleScenario(
            label="Medication refill visit — Marcus Webb",
            patient_id="pt-1003",
            provider_id="dr-chen",
            raw_dictation_text=(
                "Patient here for medication refill. Reflux symptoms well controlled on omeprazole "
                "with no breakthrough heartburn. Seasonal allergy symptoms mild this week, using "
                "loratadine as needed. No new complaints today. Plan is to refill both medications "
                "for ninety days and follow up as needed."
            ),
        ),
    ]
