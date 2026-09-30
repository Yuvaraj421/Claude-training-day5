"""In-process Event Streaming Backbone.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"Event Streaming Backbone" ("Decouples capture from processing at high
throughput", "Kafka/managed streaming platform") and key processing step #2
("Decouple ASR and LLM stages via an event streaming backbone so each stage
scales independently").

Stands in for Kafka: topics are just names, handlers subscribe to a topic,
and `publish()` dispatches synchronously to every subscriber in registration
order. That's enough to demonstrate the decoupling contract (stages only ever
communicate by publishing/consuming named events, never by calling each other
directly) without standing up a real broker for the demo.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True)
class Event:
    topic: str
    payload: dict
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._log: list[Event] = []

    def subscribe(self, topic: str, handler: Callable[[Event], None]) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: dict) -> Event:
        event = Event(topic=topic, payload=payload)
        self._log.append(event)
        for handler in self._subscribers[topic]:
            handler(event)
        return event

    def events(self, topic: str | None = None) -> list[Event]:
        if topic is None:
            return list(self._log)
        return [e for e in self._log if e.topic == topic]
