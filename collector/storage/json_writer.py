"""Persist snapshots as JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from collector.domain.models import MachineSnapshot


class JsonSnapshotWriter:
    def __init__(self, output_directory: Path) -> None:
        self._output_directory = output_directory

    def write(self, snapshot: MachineSnapshot) -> Path:
        self._output_directory.mkdir(parents=True, exist_ok=True)
        timestamp = snapshot.collected_at.strftime("%Y%m%dT%H%M%SZ")
        filename = f"snapshot_{timestamp}_{snapshot.hostname}.json"
        path = self._output_directory / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(snapshot.to_dict(), handle, indent=2)
            handle.write("\n")
        latest = self._output_directory / "latest.json"
        with latest.open("w", encoding="utf-8") as handle:
            json.dump(snapshot.to_dict(), handle, indent=2)
            handle.write("\n")
        return path
