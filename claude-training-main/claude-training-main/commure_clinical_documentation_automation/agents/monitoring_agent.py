"""Scale/Quality Monitoring agent.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"Scale/Quality Monitoring" ("Tracks throughput, latency, and note-quality
metrics across tenants") and key processing step #5 ("Track per-tenant
throughput/latency/quality metrics to detect degradation for any individual
health system within the shared multi-tenant platform").

Subscribes to every stage's topic and keeps running per-tenant counters —
it never mutates pipeline state, only observes the bus, which is what lets
it watch every tenant's throughput without being on the critical path of
any single encounter.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from agents.base import BaseAgent
from streaming import Event, EventBus


@dataclass
class TenantMetrics:
    encounters_captured: int = 0
    transcripts_completed: int = 0
    notes_generated: int = 0
    encounters_delivered: int = 0
    total_asr_latency_ms: int = 0

    @property
    def avg_asr_latency_ms(self) -> float:
        if self.transcripts_completed == 0:
            return 0.0
        return round(self.total_asr_latency_ms / self.transcripts_completed, 1)


class MonitoringAgent(BaseAgent):
    name = "MonitoringAgent"

    def __init__(self, bus: EventBus):
        self._metrics: dict[str, TenantMetrics] = defaultdict(TenantMetrics)
        bus.subscribe("encounter.audio", self._on_encounter_audio)
        bus.subscribe("transcript.ready", self._on_transcript_ready)
        bus.subscribe("note.generated", self._on_note_generated)
        bus.subscribe("encounter.completed", self._on_encounter_completed)

    def _on_encounter_audio(self, event: Event) -> None:
        self._metrics[event.payload["tenant_id"]].encounters_captured += 1

    def _on_transcript_ready(self, event: Event) -> None:
        metrics = self._metrics[event.payload["tenant_id"]]
        metrics.transcripts_completed += 1
        metrics.total_asr_latency_ms += event.payload["latency_ms"]

    def _on_note_generated(self, event: Event) -> None:
        self._metrics[event.payload["tenant_id"]].notes_generated += 1

    def _on_encounter_completed(self, event: Event) -> None:
        self._metrics[event.payload["tenant_id"]].encounters_delivered += 1

    def get_metrics(self, tenant_id: str) -> TenantMetrics:
        return self._metrics[tenant_id]
