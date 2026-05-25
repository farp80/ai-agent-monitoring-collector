"""Collector interface — one metric category per implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class ICollector(ABC):
    """Single responsibility: enrich a snapshot with one data category."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier used in config enabled_collectors."""

    @abstractmethod
    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        """Mutate snapshot in place with collected data."""
