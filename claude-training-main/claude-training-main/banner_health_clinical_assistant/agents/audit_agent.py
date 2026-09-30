"""Audit / compliance logging agent.

Doc reference: 01-banner-health-clinical-documentation.md, component "Audit / Compliance Log"
("Immutable trail of AI-generated vs. human-edited content").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from agents.base import BaseAgent


@dataclass(frozen=True)
class AuditEvent:
    encounter_id: str
    event_type: str
    detail: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditAgent(BaseAgent):
    name = "AuditAgent"

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log(self, encounter_id: str, event_type: str, detail: str) -> AuditEvent:
        event = AuditEvent(encounter_id=encounter_id, event_type=event_type, detail=detail)
        self._events.append(event)
        return event

    def events_for(self, encounter_id: str) -> List[AuditEvent]:
        return [e for e in self._events if e.encounter_id == encounter_id]
