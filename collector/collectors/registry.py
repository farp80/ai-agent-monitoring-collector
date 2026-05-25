"""Registry of collectors — extend by registering new ICollector instances."""

from __future__ import annotations

from collector.collectors.base import ICollector
from collector.collectors.hard_drives import HardDrivesCollector
from collector.collectors.ip_addresses import IpAddressesCollector
from collector.collectors.mac_address import MacAddressCollector
from collector.collectors.network_adapters import NetworkAdaptersCollector
from collector.collectors.serial_number import SerialNumberCollector
from collector.config.settings import AppSettings


class CollectorRegistry:
    def __init__(self) -> None:
        self._collectors: dict[str, ICollector] = {}

    def register(self, collector: ICollector) -> None:
        self._collectors[collector.name] = collector

    def all(self) -> list[ICollector]:
        return list(self._collectors.values())

    def resolve(self, enabled_names: list[str] | None) -> list[ICollector]:
        if enabled_names is None:
            return self.all()
        missing = [name for name in enabled_names if name not in self._collectors]
        if missing:
            known = ", ".join(sorted(self._collectors))
            raise ValueError(f"Unknown collector(s): {', '.join(missing)}. Known: {known}")
        return [self._collectors[name] for name in enabled_names]


def build_default_registry(settings: AppSettings) -> CollectorRegistry:
    registry = CollectorRegistry()
    registry.register(SerialNumberCollector())
    registry.register(IpAddressesCollector(settings))
    registry.register(MacAddressCollector())
    registry.register(HardDrivesCollector())
    registry.register(NetworkAdaptersCollector())
    return registry
