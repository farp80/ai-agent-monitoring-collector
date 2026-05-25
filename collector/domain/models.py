"""Domain models for collected machine data."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class IpAddresses:
    public: str | None
    private: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardDrive:
    device_id: str
    model: str | None = None
    serial_number: str | None = None
    size_bytes: int | None = None
    media_type: str | None = None
    interface_type: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NetworkAdapter:
    name: str
    mac_address: str | None
    adapter_type: str  # wired | wireless | other
    is_up: bool | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MachineSnapshot:
    """Aggregated snapshot from all collectors for one collection cycle."""

    collected_at: datetime
    platform: str
    hostname: str
    serial_number: str | None = None
    ip_addresses: IpAddresses | None = None
    mac_addresses: list[str] = field(default_factory=list)
    hard_drives: list[HardDrive] = field(default_factory=list)
    network_adapters: list[NetworkAdapter] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        def serialize(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.astimezone(timezone.utc).isoformat()
            if hasattr(value, "__dataclass_fields__"):
                return {k: serialize(v) for k, v in asdict(value).items()}
            if isinstance(value, list):
                return [serialize(item) for item in value]
            if isinstance(value, dict):
                return {k: serialize(v) for k, v in value.items()}
            return value

        return serialize(
            {
                "collected_at": self.collected_at,
                "platform": self.platform,
                "hostname": self.hostname,
                "serial_number": self.serial_number,
                "ip_addresses": self.ip_addresses,
                "mac_addresses": self.mac_addresses,
                "hard_drives": self.hard_drives,
                "network_adapters": self.network_adapters,
                "extra": self.extra,
            }
        )

    @staticmethod
    def empty_shell(platform: str, hostname: str) -> MachineSnapshot:
        return MachineSnapshot(
            collected_at=datetime.now(timezone.utc),
            platform=platform,
            hostname=hostname,
        )
