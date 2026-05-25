from collector.collectors.base import ICollector
from collector.config.settings import AppSettings
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class IpAddressesCollector(ICollector):
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def name(self) -> str:
        return "ip_addresses"

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.ip_addresses = provider.get_ip_addresses(
            self._settings.public_ip_lookup_url,
            self._settings.public_ip_timeout_seconds,
        )
