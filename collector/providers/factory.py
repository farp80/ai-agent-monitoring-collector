"""Factory for platform-specific providers."""

from __future__ import annotations

from collector.platform.detector import PlatformDetector, PlatformKind
from collector.providers.base import IPlatformProvider
from collector.providers.chromeos_provider import ChromeOsPlatformProvider
from collector.providers.darwin_provider import DarwinPlatformProvider
from collector.providers.linux_provider import LinuxPlatformProvider
from collector.providers.windows_provider import WindowsPlatformProvider


class PlatformProviderFactory:
    """Single responsibility: construct the correct IPlatformProvider."""

    def __init__(self, detector: PlatformDetector | None = None) -> None:
        self._detector = detector or PlatformDetector()

    def create(self) -> IPlatformProvider:
        kind = self._detector.detect()
        if kind == PlatformKind.WINDOWS:
            return WindowsPlatformProvider()
        if kind == PlatformKind.DARWIN:
            return DarwinPlatformProvider()
        if kind == PlatformKind.CHROMEOS:
            return ChromeOsPlatformProvider()
        if kind == PlatformKind.LINUX:
            return LinuxPlatformProvider()
        return LinuxPlatformProvider()
