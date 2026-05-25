"""Windows platform provider."""

from __future__ import annotations

import json
import re
import socket
import uuid

from collector.domain.models import HardDrive, IpAddresses, NetworkAdapter
from collector.providers._command import run_command
from collector.providers.base import IPlatformProvider


class WindowsPlatformProvider(IPlatformProvider):
    @property
    def platform_label(self) -> str:
        return "windows"

    def get_hostname(self) -> str:
        return socket.gethostname()

    def get_serial_number(self) -> str | None:
        output = self._powershell(
            "(Get-CimInstance Win32_BIOS).SerialNumber"
        )
        if output and output.lower() not in {"none", "to be filled by o.e.m.", "unknown", ""}:
            return output
        return None

    def get_ip_addresses(self, public_lookup_url: str, timeout_seconds: float) -> IpAddresses:
        from collector.providers._unix import UnixNetworkMixin

        mixin = UnixNetworkMixin()
        public = mixin._fetch_public_ip(public_lookup_url, timeout_seconds)
        private: list[str] = []
        output = run_command(["ipconfig"])
        if output:
            for match in re.finditer(r"IPv4 Address[^:]*:\s*([\d.]+)", output, re.IGNORECASE):
                ip = match.group(1)
                if not ip.startswith("127.") and ip not in private:
                    private.append(ip)
        if not private:
            private = mixin._private_ips()
        return IpAddresses(public=public, private=private)

    def get_mac_addresses(self) -> list[str]:
        macs: list[str] = []
        for adapter in self.get_network_adapters():
            if adapter.mac_address and adapter.mac_address not in macs:
                macs.append(adapter.mac_address)
        node = uuid.getnode()
        fallback = ":".join(f"{(node >> elements) & 0xFF:02x}" for elements in range(40, -8, -8))
        if fallback and fallback not in macs and fallback != "00:00:00:00:00:00":
            macs.append(fallback)
        return macs

    def get_hard_drives(self) -> list[HardDrive]:
        script = (
            "Get-CimInstance Win32_DiskDrive | "
            "Select-Object DeviceID,Model,SerialNumber,Size,MediaType,InterfaceType | "
            "ConvertTo-Json -Compress"
        )
        output = self._powershell(script)
        if not output:
            return []
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return []
        if isinstance(payload, dict):
            payload = [payload]
        drives: list[HardDrive] = []
        for item in payload:
            size_raw = item.get("Size")
            size_bytes = int(size_raw) if size_raw not in (None, "") else None
            drives.append(
                HardDrive(
                    device_id=str(item.get("DeviceID", "unknown")),
                    model=item.get("Model"),
                    serial_number=item.get("SerialNumber"),
                    size_bytes=size_bytes,
                    media_type=item.get("MediaType"),
                    interface_type=item.get("InterfaceType"),
                )
            )
        return drives

    def get_network_adapters(self) -> list[NetworkAdapter]:
        script = (
            "Get-NetAdapter | "
            "Select-Object Name,MacAddress,Status,InterfaceDescription,PhysicalMediaType | "
            "ConvertTo-Json -Compress"
        )
        output = self._powershell(script)
        if not output:
            return self._adapters_from_getmac()
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return self._adapters_from_getmac()
        if isinstance(payload, dict):
            payload = [payload]
        adapters: list[NetworkAdapter] = []
        for item in payload:
            name = str(item.get("Name", "unknown"))
            mac = item.get("MacAddress")
            if mac:
                mac = str(mac).replace("-", ":").lower()
            adapter_type = self._classify_windows_adapter(item)
            status = str(item.get("Status", "")).lower()
            adapters.append(
                NetworkAdapter(
                    name=name,
                    mac_address=mac,
                    adapter_type=adapter_type,
                    is_up=status == "up",
                    extra={"interface_description": item.get("InterfaceDescription")},
                )
            )
        return adapters

    def _adapters_from_getmac(self) -> list[NetworkAdapter]:
        output = run_command(["getmac", "/fo", "csv", "/nh"])
        if not output:
            return []
        adapters: list[NetworkAdapter] = []
        for line in output.splitlines():
            parts = [p.strip('"') for p in line.split(",")]
            if len(parts) >= 2:
                adapters.append(
                    NetworkAdapter(
                        name=parts[1] if len(parts) > 1 else "adapter",
                        mac_address=parts[0].replace("-", ":").lower(),
                        adapter_type="other",
                    )
                )
        return adapters

    @staticmethod
    def _classify_windows_adapter(item: dict) -> str:
        description = str(item.get("InterfaceDescription", "")).lower()
        media = str(item.get("PhysicalMediaType", "")).lower()
        if "wireless" in description or "wi-fi" in description or "802.11" in description:
            return "wireless"
        if "ethernet" in description or media == "802.3":
            return "wired"
        return "other"

    def _powershell(self, script: str) -> str | None:
        return run_command(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            timeout=60.0,
        )
