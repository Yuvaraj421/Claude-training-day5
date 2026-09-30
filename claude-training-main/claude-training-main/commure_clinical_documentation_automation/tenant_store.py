"""In-memory Tenant Config & Template Service.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"Tenant Config & Template Service" ("Stores per-health-system note templates,
specialty configs, EHR mapping").

Stands in for a real multi-tenant config service: no network calls, just a
small registry so the demo can run end-to-end offline across several
synthetic health-system tenants with different EHR vendors and templates.
"""

from __future__ import annotations

from typing import Optional

from models import EHRVendor, NoteTemplate, Tenant


class TenantConfigService:
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def register_tenant(self, health_system_name: str, ehr_vendor: EHRVendor, data_residency_region: str) -> Tenant:
        tenant = Tenant(
            health_system_name=health_system_name,
            ehr_vendor=ehr_vendor,
            data_residency_region=data_residency_region,
        )
        self._tenants[tenant.id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> list[Tenant]:
        return list(self._tenants.values())

    def find_tenant(self, name_or_id: str) -> Optional[Tenant]:
        """Resolves a tenant by exact id first, then a unique case-insensitive
        substring match on health_system_name. Returns None if the id is
        unknown and the name is missing, ambiguous, or matches nothing —
        callers should treat that as "ask the user which tenant they meant"
        rather than guessing."""
        tenant = self.get_tenant(name_or_id)
        if tenant is not None:
            return tenant
        needle = name_or_id.strip().lower()
        matches = [t for t in self._tenants.values() if needle in t.health_system_name.lower()]
        return matches[0] if len(matches) == 1 else None

    def require_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        if tenant is None:
            raise KeyError(f"Unknown tenant_id: {tenant_id}")
        return tenant

    def set_template(self, tenant_id: str, specialty: str, section_schema: list[str]) -> NoteTemplate:
        tenant = self.require_tenant(tenant_id)
        template = NoteTemplate(tenant_id=tenant_id, specialty=specialty, section_schema=section_schema)
        tenant.note_templates[specialty] = template
        return template

    def get_template(self, tenant_id: str, specialty: str) -> NoteTemplate:
        tenant = self.require_tenant(tenant_id)
        template = tenant.note_templates.get(specialty)
        if template is None:
            # Fall back to a generic SOAP-style schema so an unconfigured
            # specialty still produces a usable note.
            template = NoteTemplate(
                tenant_id=tenant_id,
                specialty=specialty,
                section_schema=["subjective", "objective", "assessment", "plan"],
            )
        return template
