"""ASR Service Pool agent.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"ASR Service Pool" ("Horizontally scaled transcription workers") and key
processing step #2 ("Decouple ASR and LLM stages via an event streaming
backbone so each stage scales independently").

Subscribes to `encounter.audio` and publishes `transcript.ready` — it never
calls the documentation agent directly, only the bus. A synthetic
`asr_worker_id` and `latency_ms` stand in for the worker-pool assignment and
timing a real auto-scaled ASR fleet would report.
"""

from __future__ import annotations

import random

from agents.base import BaseAgent
from encounter_store import EncounterStore
from models import EncounterStatus, Transcript
from streaming import Event, EventBus

_WORKER_POOL_SIZE = 8


class TranscriptionAgent(BaseAgent):
    name = "TranscriptionAgent"

    def __init__(self, encounter_store: EncounterStore, bus: EventBus):
        self.encounter_store = encounter_store
        self.bus = bus
        bus.subscribe("encounter.audio", self._on_encounter_audio)

    def _on_encounter_audio(self, event: Event) -> None:
        self.transcribe(
            tenant_id=event.payload["tenant_id"],
            encounter_id=event.payload["encounter_id"],
            audio_text=event.payload["audio_text"],
        )

    def transcribe(self, tenant_id: str, encounter_id: str, audio_text: str) -> Transcript:
        encounter = self.encounter_store.get_encounter(tenant_id, encounter_id)
        encounter.status = EncounterStatus.TRANSCRIBING

        rng = random.Random(encounter_id)  # deterministic worker/latency per encounter
        transcript = Transcript(
            encounter_id=encounter_id,
            tenant_id=tenant_id,
            text=audio_text.strip(),
            asr_worker_id=f"asr-worker-{rng.randint(0, _WORKER_POOL_SIZE - 1)}",
            latency_ms=rng.randint(150, 900),
        )
        self.encounter_store.save_transcript(transcript)
        self.bus.publish(
            "transcript.ready",
            {
                "tenant_id": tenant_id,
                "encounter_id": encounter_id,
                "transcript_id": transcript.id,
                "latency_ms": transcript.latency_ms,
            },
        )
        return transcript
