import pytest

from encounter_store import EncounterStore, TenantIsolationError
from models import Encounter, GeneratedNote, GeneratedBy, Transcript


def test_cross_tenant_encounter_read_is_blocked():
    store = EncounterStore()
    encounter = Encounter(tenant_id="tenant-a", clinician_id="dr-chen", specialty="primary_care")
    store.save_encounter(encounter)

    assert store.get_encounter("tenant-a", encounter.id) is encounter
    with pytest.raises(TenantIsolationError):
        store.get_encounter("tenant-b", encounter.id)


def test_cross_tenant_transcript_read_is_blocked():
    store = EncounterStore()
    transcript = Transcript(
        encounter_id="enc-1", tenant_id="tenant-a", text="hello", asr_worker_id="asr-worker-0", latency_ms=200
    )
    store.save_transcript(transcript)

    with pytest.raises(TenantIsolationError):
        store.get_transcript("tenant-b", transcript.id)


def test_cross_tenant_note_read_is_blocked():
    store = EncounterStore()
    note = GeneratedNote(
        encounter_id="enc-1", tenant_id="tenant-a", content_sections={"plan": "x"}, generated_by=GeneratedBy.MOCK
    )
    store.save_note(note)

    with pytest.raises(TenantIsolationError):
        store.get_note("tenant-b", note.id)
    with pytest.raises(TenantIsolationError):
        store.get_note_for_encounter("tenant-b", "enc-1")


def test_unknown_encounter_id_raises_key_error_not_isolation_error():
    store = EncounterStore()
    with pytest.raises(KeyError):
        store.get_encounter("tenant-a", "does-not-exist")
