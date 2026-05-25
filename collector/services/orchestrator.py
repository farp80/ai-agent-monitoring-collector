"""Orchestrates a full collection cycle."""

from __future__ import annotations

from datetime import datetime, timezone

from collector.collectors.registry import CollectorRegistry
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class CollectionOrchestrator:
    def __init__(
        self,
        registry: CollectorRegistry,
        provider: IPlatformProvider,
        enabled_collectors: list[str] | None = None,
    ) -> None:
        self._collectors = registry.resolve(enabled_collectors)
        self._provider = provider

    def run(self) -> MachineSnapshot:
        snapshot = MachineSnapshot.empty_shell(
            platform=self._provider.platform_label,
            hostname=self._provider.get_hostname(),
        )
        snapshot.collected_at = datetime.now(timezone.utc)

        for collector in self._collectors:
            collector.collect(snapshot, self._provider)

        return snapshot
