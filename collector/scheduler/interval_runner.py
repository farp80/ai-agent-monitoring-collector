"""Run collection on a configurable interval."""

from __future__ import annotations

import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


class IntervalRunner:
    def __init__(self, interval_minutes: float, task: Callable[[], None]) -> None:
        if interval_minutes <= 0:
            raise ValueError("collection_interval_minutes must be greater than zero")
        self._interval_seconds = interval_minutes * 60.0
        self._task = task

    def run_forever(self) -> None:
        logger.info("Starting collection loop every %.2f minute(s)", self._interval_seconds / 60)
        while True:
            self._run_once_safe()
            time.sleep(self._interval_seconds)

    def run_once(self) -> None:
        self._run_once_safe()

    def _run_once_safe(self) -> None:
        try:
            self._task()
        except Exception:
            logger.exception("Collection cycle failed")
