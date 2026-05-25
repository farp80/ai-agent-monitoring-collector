"""Shared Unix-like (Linux, macOS, ChromeOS) collection logic."""

from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from pathlib import Path

from collector.domain.models import HardDrive, IpAddresses, NetworkAdapter
from collector.providers._command import run_command


class UnixNetworkMixin:
    """Reusable IP, MAC, and adapter discovery for Unix-like systems."""

    SYS_CLASS_NET = Path("/sys/class/net")

    def _fetch_public_ip(self, url: str, timeout_seconds: float) -> str | None:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "machine-collector/0.1"})
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, OSError, TimeoutError, ValueError):
            return None
        try:
            payload = json.loads(body)
            if isinstance(payload, dict) and "ip" in payload:
                return str(payload["ip"])
        except json.JSONDecodeError:
            pass
        candidate = body.strip()
        return candidate if candidate else None

    def _private_ips(self) -> list[str]:
        addresses: list[str] = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ip and ":" not in ip and not ip.startswith("127."):
                    if ip not in addresses:
                        addresses.append(ip)
        except OSError:
            pass

        output = run_command(["hostname", "-I"])
        if output:
            for token in output.split():
                if token and token not in addresses and not token.startswith("127."):
                    addresses.append(token)
        return addresses

    def get_ip_addresses(self, public_lookup_url: str, timeout_seconds: float) -> IpAddresses:
        return IpAddresses(
            public=self._fetch_public_ip(public_lookup_url, timeout_seconds),
            private=self._private_ips(),
        )

    def _iter_net_interfaces(self) -> list[tuple[str, str | None, str]]:
        adapters: list[tuple[str, str | None, str]] = []
        if not self.SYS_CLASS_NET.exists():
            return adapters

        for iface_dir in sorted(self.SYS_CLASS_NET.iterdir()):
            name = iface_dir.name
            if name == "lo":
                continue
            address_file = iface_dir / "address"
            mac = None
            if address_file.exists():
                mac = address_file.read_text(encoding="utf-8", errors="ignore").strip() or None
            adapter_type = self._classify_adapter(name, iface_dir)
            adapters.append((name, mac, adapter_type))
        return adapters

    def _classify_adapter(self, name: str, iface_dir: Path) -> str:
        wireless = iface_dir / "wireless"
        if wireless.exists() or name.startswith(("wlan", "wlp", "wifi")):
            return "wireless"
        if name.startswith(("eth", "en", "eno", "ens")):
            return "wired"
        return "other"

    def get_mac_addresses(self) -> list[str]:
        macs: list[str] = []
        for _, mac, _ in self._iter_net_interfaces():
            if mac and mac != "00:00:00:00:00:00" and mac not in macs:
                macs.append(mac)
        return macs

    def get_network_adapters(self) -> list[NetworkAdapter]:
        adapters: list[NetworkAdapter] = []
        for name, mac, adapter_type in self._iter_net_interfaces():
            operstate = self.SYS_CLASS_NET / name / "operstate"
            is_up = None
            if operstate.exists():
                state = operstate.read_text(encoding="utf-8", errors="ignore").strip().lower()
                is_up = state == "up"
            adapters.append(
                NetworkAdapter(
                    name=name,
                    mac_address=mac,
                    adapter_type=adapter_type,
                    is_up=is_up,
                )
            )
        return adapters


class LinuxStorageMixin:
    """Disk discovery via lsblk on Linux and ChromeOS."""

    def get_hard_drives(self) -> list[HardDrive]:
        output = run_command(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL,SERIAL,ROTA,TRAN"])
        if not output:
            return self._hard_drives_from_sys_block()
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return self._hard_drives_from_sys_block()

        drives: list[HardDrive] = []
        for device in payload.get("blockdevices", []):
            if device.get("type") != "disk":
                continue
            rota = device.get("rota")
            media = "hdd" if rota == "1" else "ssd" if rota == "0" else None
            drives.append(
                HardDrive(
                    device_id=device.get("name", "unknown"),
                    model=device.get("model"),
                    serial_number=device.get("serial"),
                    size_bytes=self._parse_size(device.get("size")),
                    media_type=media,
                    interface_type=device.get("tran"),
                )
            )
        return drives

    def _hard_drives_from_sys_block(self) -> list[HardDrive]:
        drives: list[HardDrive] = []
        block_path = Path("/sys/block")
        if not block_path.exists():
            return drives
        for entry in sorted(block_path.iterdir()):
            if entry.name.startswith("loop"):
                continue
            size_file = entry / "size"
            size_bytes = None
            if size_file.exists():
                try:
                    sectors = int(size_file.read_text().strip())
                    size_bytes = sectors * 512
                except ValueError:
                    pass
            drives.append(HardDrive(device_id=entry.name, size_bytes=size_bytes))
        return drives

    @staticmethod
    def _parse_size(size_value: str | None) -> int | None:
        if not size_value:
            return None
        match = re.match(r"^([\d.]+)([KMGTP]?)$", str(size_value).upper())
        if not match:
            return None
        number = float(match.group(1))
        unit = match.group(2) or "B"
        multipliers = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4, "P": 1024**5}
        return int(number * multipliers.get(unit, 1))
