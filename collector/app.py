"""Application composition root."""

from __future__ import annotations

import logging
import sys

from collector.collectors.registry import build_default_registry
from collector.config.settings import AppSettings, load_settings
from collector.providers.factory import PlatformProviderFactory
from collector.scheduler.interval_runner import IntervalRunner
from collector.services.orchestrator import CollectionOrchestrator
from collector.storage.json_writer import JsonSnapshotWriter

logger = logging.getLogger(__name__)


class CollectorApplication:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or load_settings()
        self._provider_factory = PlatformProviderFactory()
        self._registry = build_default_registry(self.settings)

    def run(self) -> int:
        self._configure_logging()
        provider = self._provider_factory.create()
        writer = JsonSnapshotWriter(self.settings.output_directory)
        orchestrator = CollectionOrchestrator(
            self._registry,
            provider,
            self.settings.enabled_collectors,
        )

        def cycle() -> None:
            snapshot = orchestrator.run()
            path = writer.write(snapshot)
            logger.info("Wrote snapshot to %s", path)

        runner = IntervalRunner(self.settings.collection_interval_minutes, cycle)
        if self.settings.run_once:
            runner.run_once()
        else:
            runner.run_forever()
        return 0

    @staticmethod
    def _configure_logging() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
        )
