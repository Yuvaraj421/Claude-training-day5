"""Shared interface for per-vendor EHR adapters.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"EHR Adapter Layer" ("Normalizes integration across many different EHR
vendors", "Adapter-per-EHR-vendor pattern") and key processing step #4
("Abstract EHR differences behind a per-vendor adapter layer so the
documentation pipeline itself stays EHR-agnostic").
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models import GeneratedNote, Tenant


class EHRAdapter(ABC):
    vendor: str = "base"

    @abstractmethod
    def push_note(self, tenant: Tenant, note: GeneratedNote) -> str:
        """Push a finalized note to the tenant's EHR and return the resulting document ID."""
