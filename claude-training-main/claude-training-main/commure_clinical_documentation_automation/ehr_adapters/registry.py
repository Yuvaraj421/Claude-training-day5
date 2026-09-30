"""Routes a tenant's `ehr_vendor` to its adapter instance.

Doc reference: 05-commure-clinical-documentation-automation.md — the EHR
Adapter Layer sits between the shared LLM Documentation Service Pool and
each tenant's actual EHR system; this registry is the routing table that
keeps the pipeline itself EHR-agnostic.
"""

from __future__ import annotations

from models import EHRVendor

from .athenahealth_adapter import AthenahealthAdapter
from .base import EHRAdapter
from .cerner_adapter import CernerAdapter
from .epic_adapter import EpicAdapter


class UnsupportedEHRVendorError(Exception):
    pass


class EHRAdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, EHRAdapter] = {
            EHRVendor.EPIC.value: EpicAdapter(),
            EHRVendor.CERNER.value: CernerAdapter(),
            EHRVendor.ATHENAHEALTH.value: AthenahealthAdapter(),
        }

    def get(self, ehr_vendor: EHRVendor) -> EHRAdapter:
        adapter = self._adapters.get(ehr_vendor.value)
        if adapter is None:
            raise UnsupportedEHRVendorError(f"No adapter registered for EHR vendor: {ehr_vendor}")
        return adapter
