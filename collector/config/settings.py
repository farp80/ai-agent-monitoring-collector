"""Application configuration loaded from JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config/config.json")


@dataclass
class AppSettings:
    collection_interval_minutes: float = 15.0
    output_directory: Path = field(default_factory=lambda: Path("data"))
    config_path: Path = field(default_factory=lambda: DEFAULT_CONFIG_PATH)
    enabled_collectors: list[str] | None = None
    public_ip_lookup_url: str = "https://api.ipify.org?format=json"
    public_ip_timeout_seconds: float = 5.0
    run_once: bool = False

    @classmethod
    def from_dict(cls, data: dict, config_path: Path) -> AppSettings:
        interval = float(data.get("collection_interval_minutes", 15))
        if interval <= 0:
            raise ValueError(
                "collection_interval_minutes must be greater than zero "
                f"(got {interval} in {config_path})"
            )
        output = Path(data.get("output_directory", "data"))
        enabled = data.get("enabled_collectors")
        if enabled is not None and not isinstance(enabled, list):
            raise ValueError("enabled_collectors must be a list of collector names or null")

        return cls(
            collection_interval_minutes=interval,
            output_directory=output,
            config_path=config_path,
            enabled_collectors=enabled,
            public_ip_lookup_url=str(
                data.get("public_ip_lookup_url", "https://api.ipify.org?format=json")
            ),
            public_ip_timeout_seconds=float(data.get("public_ip_timeout_seconds", 5)),
            run_once=bool(data.get("run_once", False)),
        )


def load_settings(path: Path | None = None) -> AppSettings:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return AppSettings(config_path=config_path)

    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return AppSettings.from_dict(data, config_path)
