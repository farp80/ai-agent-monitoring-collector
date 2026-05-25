"""Abstract platform provider — OS-specific data access."""

from __future__ import annotations

from abc import ABC, abstractmethod

from collector.domain.models import HardDrive, IpAddresses, NetworkAdapter


class IPlatformProvider(ABC):
    """Contract for reading machine attributes on a specific OS."""

    @property
    @abstractmethod
    def platform_label(self) -> str:
        """Human-readable platform identifier stored in snapshots."""

    @abstractmethod
    def get_hostname(self) -> str:
        ...

    @abstractmethod
    def get_serial_number(self) -> str | None:
        ...

    @abstractmethod
    def get_ip_addresses(self, public_lookup_url: str, timeout_seconds: float) -> IpAddresses:
        ...

    @abstractmethod
    def get_mac_addresses(self) -> list[str]:
        ...

    @abstractmethod
    def get_hard_drives(self) -> list[HardDrive]:
        ...

    @abstractmethod
    def get_network_adapters(self) -> list[NetworkAdapter]:
        ...
