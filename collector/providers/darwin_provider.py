"""macOS (Darwin) platform provider."""

from __future__ import annotations

import plistlib
import re
import socket

from collector.domain.models import HardDrive, NetworkAdapter
from collector.providers._command import run_command
from collector.providers._unix import UnixNetworkMixin
from collector.providers.base import IPlatformProvider


class DarwinPlatformProvider(IPlatformProvider, UnixNetworkMixin):
    @property
    def platform_label(self) -> str:
        return "darwin"

    def get_hostname(self) -> str:
        return socket.gethostname()

    def get_serial_number(self) -> str | None:
        output = run_command(
            ["system_profiler", "SPHardwareDataType"],
            timeout=60.0,
        )
        if not output:
            return None
        match = re.search(r"Serial Number \(system\):\s*(.+)", output, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def get_hard_drives(self) -> list[HardDrive]:
        plist_output = run_command(["diskutil", "list", "-plist"])
        if plist_output:
            drives = self._hard_drives_from_diskutil_plist(plist_output)
            if drives:
                return drives
        return self._hard_drives_from_diskutil_text()

    def _hard_drives_from_diskutil_plist(self, plist_output: str) -> list[HardDrive]:
        """Parse diskutil list -plist (XML plist with AllDisksAndPartitions)."""
        try:
            payload = plistlib.loads(plist_output.encode("utf-8"))
        except (plistlib.InvalidFileException, ValueError, OSError, TypeError):
            return []

        drives: list[HardDrive] = []
        for item in payload.get("AllDisksAndPartitions", []):
            if not isinstance(item, dict):
                continue
            device_id = item.get("DeviceIdentifier")
            if not device_id or not re.fullmatch(r"disk\d+", str(device_id)):
                continue
            size_raw = item.get("Size")
            size_bytes = size_raw if isinstance(size_raw, int) else None
            drives.append(
                HardDrive(
                    device_id=str(device_id),
                    size_bytes=size_bytes,
                    extra={"partition_scheme": item.get("Content")}
                    if item.get("Content")
                    else {},
                )
            )
        return drives

    def _hard_drives_from_diskutil_text(self) -> list[HardDrive]:
        output = run_command(["diskutil", "list"])
        if not output:
            return []
        drives: list[HardDrive] = []
        for line in output.splitlines():
            if line.strip().startswith("/dev/disk"):
                device_id = line.split()[0].replace("/dev/", "")
                drives.append(HardDrive(device_id=device_id))
        return drives

    def get_network_adapters(self) -> list[NetworkAdapter]:
        adapters = super().get_network_adapters()
        if adapters:
            return adapters
        output = run_command(["networksetup", "-listallhardwareports"])
        if not output:
            return []
        return self._parse_networksetup(output)

    @staticmethod
    def _parse_networksetup(text: str) -> list[NetworkAdapter]:
        adapters: list[NetworkAdapter] = []
        current_name = ""
        current_type = "other"
        current_mac: str | None = None

        for line in text.splitlines():
            if line.startswith("Hardware Port:"):
                if current_name:
                    adapters.append(
                        NetworkAdapter(
                            name=current_name,
                            mac_address=current_mac,
                            adapter_type=current_type,
                        )
                    )
                port = line.split(":", 1)[-1].strip()
                current_name = port
                lowered = port.lower()
                if "wi-fi" in lowered or "airport" in lowered:
                    current_type = "wireless"
                elif "ethernet" in lowered or "thunderbolt" in lowered:
                    current_type = "wired"
                else:
                    current_type = "other"
                current_mac = None
            elif line.strip().startswith("Ethernet Address:"):
                current_mac = line.split(":", 1)[-1].strip()

        if current_name:
            adapters.append(
                NetworkAdapter(
                    name=current_name,
                    mac_address=current_mac,
                    adapter_type=current_type,
                )
            )
        return adapters
