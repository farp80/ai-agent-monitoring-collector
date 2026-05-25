"""Linux platform provider."""

from __future__ import annotations

import socket
from pathlib import Path

from collector.domain.models import HardDrive
from collector.providers._command import run_command
from collector.providers._unix import LinuxStorageMixin, UnixNetworkMixin
from collector.providers.base import IPlatformProvider

DMI_SERIAL = Path("/sys/class/dmi/id/product_serial")


class LinuxPlatformProvider(IPlatformProvider, UnixNetworkMixin, LinuxStorageMixin):
    @property
    def platform_label(self) -> str:
        return "linux"

    def get_hostname(self) -> str:
        return socket.gethostname()

    def get_serial_number(self) -> str | None:
        if DMI_SERIAL.exists():
            serial = DMI_SERIAL.read_text(encoding="utf-8", errors="ignore").strip()
            if serial and serial.lower() not in {"none", "to be filled by o.e.m.", "unknown"}:
                return serial
        output = run_command(["dmidecode", "-s", "system-serial-number"])
        if output and output.lower() not in {"none", "unknown"}:
            return output
        return None
