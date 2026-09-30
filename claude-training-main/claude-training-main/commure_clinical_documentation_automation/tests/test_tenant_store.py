from models import EHRVendor
from tenant_store import TenantConfigService


def test_find_tenant_by_exact_id():
    store = TenantConfigService()
    tenant = store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")
    assert store.find_tenant(tenant.id) is tenant


def test_find_tenant_by_unique_name_substring_case_insensitive():
    store = TenantConfigService()
    tenant = store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")
    assert store.find_tenant("riverside") is tenant


def test_find_tenant_returns_none_for_ambiguous_substring():
    store = TenantConfigService()
    store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")
    store.register_tenant("Riverside Regional Clinics", EHRVendor.CERNER, "us-west")
    assert store.find_tenant("riverside") is None


def test_find_tenant_returns_none_when_no_match():
    store = TenantConfigService()
    store.register_tenant("Riverside Health Network", EHRVendor.EPIC, "us-east")
    assert store.find_tenant("nonexistent") is None
