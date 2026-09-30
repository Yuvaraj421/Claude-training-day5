"""Shared base class for pipeline agents.

Each agent has a single responsibility, a `name` used for monitoring, and
communicates with the rest of the pipeline only by publishing/consuming
events on the `EventBus` (see streaming.py) — never by calling another
agent directly.
"""

from __future__ import annotations

from abc import ABC


class BaseAgent(ABC):
    name: str = "BaseAgent"
