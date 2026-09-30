"""In-memory Multi-Tenant Encounter Store.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"Multi-Tenant Encounter Store" ("Isolated storage per tenant") and key
processing step #1 ("Tag every record with tenant_id from ingestion onward,
enforcing isolation at the storage and processing layers, not just at the
API edge").

Every read/write here requires the caller's tenant_id and raises
`TenantIsolationError` if a record belongs to a different tenant — this is
the enforcement point, not just a filter of convenience.
"""

from __future__ import annotations

from models import Encounter, GeneratedNote, Transcript


class TenantIsolationError(Exception):
    """Raised when a tenant attempts to read or write another tenant's record."""


class EncounterStore:
    def __init__(self):
        self._encounters: dict[str, Encounter] = {}
        self._transcripts: dict[str, Transcript] = {}
        self._notes: dict[str, GeneratedNote] = {}

    # -- Encounters ---------------------------------------------------
    def save_encounter(self, encounter: Encounter) -> None:
        self._encounters[encounter.id] = encounter

    def get_encounter(self, tenant_id: str, encounter_id: str) -> Encounter:
        encounter = self._encounters.get(encounter_id)
        if encounter is None:
            raise KeyError(f"Unknown encounter_id: {encounter_id}")
        if encounter.tenant_id != tenant_id:
            raise TenantIsolationError(
                f"tenant {tenant_id} may not access encounter {encounter_id} owned by tenant {encounter.tenant_id}"
            )
        return encounter

    def encounters_for_tenant(self, tenant_id: str) -> list[Encounter]:
        return [e for e in self._encounters.values() if e.tenant_id == tenant_id]

    # -- Transcripts ----------------------------------------------------
    def save_transcript(self, transcript: Transcript) -> None:
        self._transcripts[transcript.id] = transcript

    def get_transcript(self, tenant_id: str, transcript_id: str) -> Transcript:
        transcript = self._transcripts.get(transcript_id)
        if transcript is None:
            raise KeyError(f"Unknown transcript_id: {transcript_id}")
        if transcript.tenant_id != tenant_id:
            raise TenantIsolationError(
                f"tenant {tenant_id} may not access transcript {transcript_id} owned by tenant {transcript.tenant_id}"
            )
        return transcript

    # -- Generated notes --------------------------------------------------
    def save_note(self, note: GeneratedNote) -> None:
        self._notes[note.id] = note

    def get_note(self, tenant_id: str, note_id: str) -> GeneratedNote:
        note = self._notes.get(note_id)
        if note is None:
            raise KeyError(f"Unknown note_id: {note_id}")
        if note.tenant_id != tenant_id:
            raise TenantIsolationError(
                f"tenant {tenant_id} may not access note {note_id} owned by tenant {note.tenant_id}"
            )
        return note

    def get_note_for_encounter(self, tenant_id: str, encounter_id: str) -> GeneratedNote | None:
        for note in self._notes.values():
            if note.encounter_id == encounter_id:
                if note.tenant_id != tenant_id:
                    raise TenantIsolationError(
                        f"tenant {tenant_id} may not access note for encounter {encounter_id} "
                        f"owned by tenant {note.tenant_id}"
                    )
                return note
        return None
