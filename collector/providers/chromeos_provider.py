"""ChromeOS platform provider (Linux-based with Chrome-specific paths)."""

from __future__ import annotations

from pathlib import Path

from collector.providers._command import run_command
from collector.providers.linux_provider import LinuxPlatformProvider

VPD_SERIAL = Path("/sys/class/vpd/serial_number")


class ChromeOsPlatformProvider(LinuxPlatformProvider):
    @property
    def platform_label(self) -> str:
        return "chromeos"

    def get_serial_number(self) -> str | None:
        if VPD_SERIAL.exists():
            serial = VPD_SERIAL.read_text(encoding="utf-8", errors="ignore").strip()
            if serial:
                return serial
        output = run_command(["vpd", "get_var", "serial_number"])
        if output:
            return output.strip()
        return super().get_serial_number()
