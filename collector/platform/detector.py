"""Detect host operating environment for provider selection."""

from __future__ import annotations

import enum
import os
import platform
from pathlib import Path


class PlatformKind(enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    CHROMEOS = "chromeos"
    UNKNOWN = "unknown"


class PlatformDetector:
    """Single responsibility: identify the current platform kind."""

    OS_RELEASE = Path("/etc/os-release")

    def detect(self) -> PlatformKind:
        system = platform.system().lower()
        if system == "windows":
            return PlatformKind.WINDOWS
        if system == "darwin":
            return PlatformKind.DARWIN
        if system == "linux":
            if self._is_chromeos():
                return PlatformKind.CHROMEOS
            return PlatformKind.LINUX
        return PlatformKind.UNKNOWN

    def label(self) -> str:
        kind = self.detect()
        if kind == PlatformKind.UNKNOWN:
            return platform.platform()
        return kind.value

    def _is_chromeos(self) -> bool:
        if os.environ.get("CHROMEOS_RELEASE_NAME"):
            return True
        if not self.OS_RELEASE.exists():
            return False
        try:
            content = self.OS_RELEASE.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            return False
        return "chromeos" in content or "chromium os" in content
