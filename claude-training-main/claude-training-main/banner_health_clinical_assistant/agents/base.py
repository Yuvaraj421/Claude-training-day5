"""Shared base class for pipeline agents.

Each agent has a single responsibility and a `name` used for audit logging.
"""

from __future__ import annotations

from abc import ABC


class BaseAgent(ABC):
    name: str = "BaseAgent"
